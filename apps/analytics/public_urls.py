from django.urls import path

from .views import EventCreateView, PageViewCreateView, VisitEndView, VisitStartView

urlpatterns = [
    path("visit-start/", VisitStartView.as_view(), name="track-visit-start"),
    path("pageview/", PageViewCreateView.as_view(), name="track-pageview"),
    path("event/", EventCreateView.as_view(), name="track-event"),
    path("visit-end/", VisitEndView.as_view(), name="track-visit-end"),
]
