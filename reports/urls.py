from django.urls import path

from reports.views import ReportSendNowView, ReportToggleDailyView

urlpatterns = [
    path("send-now/", ReportSendNowView.as_view(), name="report_send_now"),
    path("toggle-daily/", ReportToggleDailyView.as_view(), name="report_toggle_daily"),
]
