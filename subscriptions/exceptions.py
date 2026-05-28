from rest_framework.exceptions import APIException


class PaymentRequired(APIException):
    status_code = 402
    default_detail = "Подписка не активна. Требуется оплата."
    default_code = "payment_required"

