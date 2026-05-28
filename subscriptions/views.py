import json
import logging

from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClientUser
from subscriptions.models import Subscription, SubscriptionPayment, SubscriptionPlan
from subscriptions.serializers import CreatePaymentSerializer, SubscriptionPlanSerializer
from subscriptions.services import (
    activate_subscription_from_payment,
    create_yookassa_payment,
    notify_subscription_activated,
    refresh_payment_status,
)

logger = logging.getLogger(__name__)


@csrf_exempt
def yookassa_webhook(request):
    try:
        payload = json.loads((request.body or b"{}").decode("utf-8"))
        event = payload.get("event")
        payment_object = payload.get("object") if isinstance(payload.get("object"), dict) else {}
        payment_id = payment_object.get("id")

        logger.info("YooKassa webhook received event=%s payment_id=%s", event, payment_id)

        if event != "payment.succeeded":
            logger.info("YooKassa webhook ignored event=%s", event)
            return JsonResponse({"status": "ignored"}, status=200)

        if not payment_id:
            logger.error("YooKassa webhook missing payment id. payload=%s", payload)
            return JsonResponse({"status": "error", "reason": "missing_payment_id"}, status=200)

        payment = SubscriptionPayment.objects.filter(yookassa_payment_id=payment_id).first()
        if payment is None:
            logger.error("Payment not found for yookassa id=%s", payment_id)
            return JsonResponse({"status": "not_found"}, status=200)

        logger.info(
            "YooKassa webhook matched payment local_id=%s client_id=%s status=%s",
            payment.id,
            payment.client_id,
            payment.status,
        )

        if payment.status == SubscriptionPayment.Status.SUCCEEDED:
            logger.info("YooKassa webhook already processed payment_id=%s", payment.id)
            return JsonResponse({"status": "already_processed"}, status=200)

        payment.raw_payload = payment_object
        payment.save(update_fields=["raw_payload", "updated_at"])

        subscription = activate_subscription_from_payment(payment)
        if subscription is None:
            logger.error("YooKassa webhook activation failed payment_id=%s", payment.id)
            return JsonResponse({"status": "activation_failed"}, status=200)

        if subscription.plan and subscription.paid_until:
            notify_subscription_activated(client=subscription.client, plan=subscription.plan, paid_until=subscription.paid_until)

        logger.info(
            "YooKassa webhook processed successfully payment_id=%s subscription_status=%s paid_until=%s",
            payment.id,
            subscription.status,
            subscription.paid_until,
        )
        return JsonResponse({"status": "ok"}, status=200)
    except Exception:
        logger.exception("YooKassa webhook error")
        return JsonResponse({"status": "error"}, status=200)


class SubscriptionStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        client = getattr(request.user, "client", None)
        if client is None:
            return Response(
                {
                    "status": Subscription.Status.EXPIRED,
                    "client_id": None,
                    "paid_until": None,
                    "is_trial": False,
                },
                status=status.HTTP_200_OK,
            )

        subscription = Subscription.objects.filter(client=client).first()
        if not subscription:
            subscription = Subscription.objects.create(
                client=client,
                status=Subscription.Status.EXPIRED,
                paid_until=None,
                is_trial=False,
                auto_renew=True,
            )

        pending_payment = (
            SubscriptionPayment.objects
            .filter(client=client, status=SubscriptionPayment.Status.PENDING)
            .exclude(yookassa_payment_id__startswith="pending-")
            .order_by("-created_at")
            .first()
        )
        if pending_payment is not None:
            logger.info(
                "Subscription status fallback check start payment_id=%s client_id=%s",
                pending_payment.id,
                client.id,
            )
            try:
                provider_status = refresh_payment_status(pending_payment)
                logger.info(
                    "Subscription status fallback provider check payment_id=%s client_id=%s provider_status=%s",
                    pending_payment.id,
                    client.id,
                    provider_status,
                )
                if provider_status == SubscriptionPayment.Status.SUCCEEDED:
                    activated = activate_subscription_from_payment(pending_payment)
                    if activated and activated.plan and activated.paid_until:
                        notify_subscription_activated(
                            client=activated.client,
                            plan=activated.plan,
                            paid_until=activated.paid_until,
                        )
                        subscription = activated
                        logger.info(
                            "Subscription status fallback activation succeeded payment_id=%s client_id=%s",
                            pending_payment.id,
                            client.id,
                        )
                    elif activated:
                        subscription = activated
            except Exception:
                logger.exception(
                    "Subscription status fallback activation failed payment_id=%s client_id=%s",
                    pending_payment.id,
                    client.id,
                )

        if (
            subscription.status == Subscription.Status.ACTIVE
            and subscription.paid_until
            and subscription.paid_until <= timezone.now()
        ):
            subscription.status = Subscription.Status.EXPIRED
            subscription.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "status": subscription.status,
                "client_id": client.id,
                "paid_until": subscription.paid_until,
                "is_trial": subscription.is_trial,
            },
            status=status.HTTP_200_OK,
        )


class SubscriptionPlansView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by("price")
        return Response(SubscriptionPlanSerializer(plans, many=True).data, status=status.HTTP_200_OK)


class SubscriptionCreatePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsClientUser]

    def post(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = SubscriptionPlan.objects.filter(id=serializer.validated_data["plan_id"], is_active=True).first()
        if plan is None:
            return Response({"detail": "Тариф не найден."}, status=status.HTTP_404_NOT_FOUND)

        payment_data = create_yookassa_payment(client=request.client, plan=plan)
        payment = payment_data["payment"]

        return Response(
            {
                "ok": True,
                "plan": SubscriptionPlanSerializer(plan).data,
                "payment_id": payment.id,
                "yookassa_payment_id": payment.yookassa_payment_id,
                "metadata": payment_data["metadata"],
                "checkout_url": payment_data["checkout_url"],
                "confirmation_url": payment_data["confirmation_url"],
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_exempt, name="dispatch")
class YooKassaWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        django_request = getattr(request, "_request", request)
        return yookassa_webhook(django_request)


class SubscriptionWebhookView(YooKassaWebhookView):
    pass
