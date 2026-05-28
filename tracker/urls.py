from django.urls import path

from tracker.views import EventCreateView, PageViewCreateView, TrackStatsView, VisitEndView, VisitStartView

urlpatterns = [
    path("visit-start/", VisitStartView.as_view(), name="track_visit_start"),
    path("pageview/", PageViewCreateView.as_view(), name="track_pageview"),
    path("event/", EventCreateView.as_view(), name="track_event"),
    path("visit-end/", VisitEndView.as_view(), name="track_visit_end"),
    path("stats/", TrackStatsView.as_view(), name="track_stats"),
]
