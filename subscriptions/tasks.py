import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from subscriptions.models import Subscription, TelegramLink
from subscriptions.telegram import send_telegram_message

logger = logging.getLogger(__name__)


@shared_task
def notify_auto_renew_subscriptions_task() -> int:
    now = timezone.now()
    remind_before = now + timedelta(days=1)
    sent_count = 0

    subscriptions = (
        Subscription.objects.select_related("client", "plan")
        .filter(
            status=Subscription.Status.ACTIVE,
            auto_renew=True,
            paid_until__isnull=False,
            paid_until__gte=now,
            paid_until__lte=remind_before,
        )
    )

    for subscription in subscriptions:
        if subscription.plan is None:
            continue

        link = TelegramLink.objects.filter(client=subscription.client).first()
        if link is None:
            continue

        chat_id = link.telegram_chat_id or link.telegram_user_id
        if not chat_id:
            continue

        paid_until_text = timezone.localtime(subscription.paid_until).strftime("%d.%m.%Y %H:%M")
        text = (
            "Subscription is ending soon.\n"
            f"Plan: {subscription.plan.name}\n"
            f"Valid until: {paid_until_text}\n\n"
            "You can disable auto-renew from this message."
        )
        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "Disable auto-renew",
                        "callback_data": f"disable_auto_renew_{subscription.id}",
                    }
                ],
            ]
        }

        try:
            send_telegram_message(chat_id=chat_id, text=text, reply_markup=keyboard)
            sent_count += 1
        except Exception:
            logger.exception("Failed to send auto-renew reminder for subscription_id=%s", subscription.id)

    return sent_count
