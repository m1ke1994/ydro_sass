import logging
import uuid
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils import timezone
from yookassa import Configuration, Payment

from subscriptions.models import Subscription, SubscriptionPayment, SubscriptionPlan, TelegramLink
from subscriptions.telegram import send_telegram_message

logger = logging.getLogger(__name__)


def _configure_yookassa() -> None:
    shop_id = (getattr(settings, "YOOKASSA_SHOP_ID", "") or "").strip()
    secret_key = (getattr(settings, "YOOKASSA_SECRET_KEY", "") or "").strip()
    if not shop_id or not secret_key:
        raise ImproperlyConfigured("YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY must be set")
    Configuration.account_id = shop_id
    Configuration.secret_key = secret_key


def create_yookassa_payment(*, client, plan, description: str | None = None) -> dict:
    _configure_yookassa()
    amount_value = f"{plan.price:.2f}"

    payment = SubscriptionPayment.objects.create(
        client=client,
        plan=plan,
        yookassa_payment_id=f"pending-{uuid.uuid4().hex}",
        status=SubscriptionPayment.Status.PENDING,
        raw_payload={},
    )

    metadata = {
        "client_id": str(client.id),
        "plan_id": str(plan.id),
        "internal_payment_id": str(payment.id),
    }

    payload = {
        "amount": {"value": amount_value, "currency": plan.currency or "RUB"},
        "confirmation": {
            "type": "redirect",
            "return_url": getattr(settings, "YOOKASSA_RETURN_URL", "https://tracknode.ru/dashboard"),
        },
        "capture": True,
        "description": description or f"TrackNode subscription: {plan.name}",
        "metadata": metadata,
    }

    created_payment = Payment.create(payload, uuid.uuid4().hex)
    confirmation = getattr(created_payment, "confirmation", None)
    confirmation_url = getattr(confirmation, "confirmation_url", "") if confirmation is not None else ""
    provider_payment_id = getattr(created_payment, "id", "") or payment.yookassa_payment_id
    provider_status = getattr(created_payment, "status", "") or SubscriptionPayment.Status.PENDING

    payment.yookassa_payment_id = provider_payment_id
    payment.status = provider_status
    payment.raw_payload = {
        "id": provider_payment_id,
        "status": provider_status,
        "confirmation": {"confirmation_url": confirmation_url},
        "metadata": metadata,
    }
    payment.save(update_fields=["yookassa_payment_id", "status", "raw_payload", "updated_at"])

    logger.info(
        "YooKassa payment created payment_id=%s client_id=%s status=%s amount=%s",
        payment.id,
        client.id,
        payment.status,
        amount_value,
    )

    if not confirmation_url:
        return {
            "payment": payment,
            "metadata": metadata,
            "confirmation_url": "",
            "checkout_url": "",
            "error": "no_confirmation",
            "status": payment.status,
        }

    return {
        "payment": payment,
        "metadata": metadata,
        "confirmation_url": confirmation_url,
        "checkout_url": confirmation_url,
    }


def refresh_payment_status(payment: SubscriptionPayment) -> str:
    if not payment.yookassa_payment_id:
        return payment.status

    _configure_yookassa()
    provider_payment = Payment.find_one(payment.yookassa_payment_id)
    provider_status = getattr(provider_payment, "status", "") or payment.status

    payment.status = provider_status
    payment.raw_payload = {
        "id": getattr(provider_payment, "id", payment.yookassa_payment_id),
        "status": provider_status,
    }
    payment.save(update_fields=["status", "raw_payload", "updated_at"])
    logger.info(
        "YooKassa payment status refreshed payment_id=%s client_id=%s status=%s",
        payment.id,
        payment.client_id,
        payment.status,
    )
    return provider_status

def activate_subscription_from_payment(payment: SubscriptionPayment) -> Subscription | None:
    logger.info(
        "Subscription activation requested payment_id=%s client_id=%s",
        payment.id,
        payment.client_id,
    )
    try:
        with transaction.atomic():
            locked_payment = (
                SubscriptionPayment.objects
                .select_for_update()
                .filter(id=payment.id)
                .first()
            )

            if locked_payment is None:
                raise SubscriptionPayment.DoesNotExist(
                    f"SubscriptionPayment id={payment.id} not found"
                )

            if locked_payment.activated_at:
                return Subscription.objects.filter(
                    client=locked_payment.client
                ).first()

            if not locked_payment.plan_id:
                logger.error(
                    "Payment has no plan. payment_id=%s client_id=%s",
                    locked_payment.id,
                    locked_payment.client_id,
                )
                return None

            plan = SubscriptionPlan.objects.filter(id=locked_payment.plan_id).first()
            if plan is None:
                logger.error(
                    "Plan not found for payment. payment_id=%s client_id=%s plan_id=%s",
                    locked_payment.id,
                    locked_payment.client_id,
                    locked_payment.plan_id,
                )
                return None

            subscription, _ = Subscription.objects.select_for_update().get_or_create(
                client=locked_payment.client,
                defaults={
                    "status": Subscription.Status.EXPIRED,
                    "is_trial": False,
                    "auto_renew": True,
                },
            )

            now = timezone.now()

            subscription.status = Subscription.Status.ACTIVE
            subscription.plan = plan
            subscription.paid_until = now + timedelta(days=plan.duration_days)
            subscription.is_trial = False
            subscription.save()

            locked_payment.status = SubscriptionPayment.Status.SUCCEEDED
            locked_payment.activated_at = now
            locked_payment.save()

            logger.info(
                "Subscription activated successfully payment_id=%s client_id=%s",
                locked_payment.id,
                locked_payment.client_id,
            )
            return subscription
    except Exception:
        logger.exception(
            "Subscription activation failed payment_id=%s",
            payment.id,
        )
        raise


def notify_subscription_activated(client, plan, paid_until) -> None:
    link = TelegramLink.objects.filter(client=client).first()
    if link is None:
        return

    chat_id = link.telegram_chat_id or link.telegram_user_id
    if not chat_id:
        return

    paid_until_text = timezone.localtime(paid_until).strftime("%d.%m.%Y %H:%M") if paid_until else "-"
    text = (
        "🎉 Подписка активирована!\n\n"
        f"Тариф: {plan.name}\n"
        f"Действует до: {paid_until_text}\n\n"
        "Теперь вам доступна вся аналитика TrackNode 🚀"
    )
    send_telegram_message(chat_id=chat_id, text=text)

