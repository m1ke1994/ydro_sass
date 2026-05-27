from django.urls import path

from .views import ClientMediaDeleteView, ClientMediaListView, ClientMediaUploadView, UploadFileView

urlpatterns = [
    path("", ClientMediaListView.as_view(), name="client-media-list"),
    path("upload/", ClientMediaUploadView.as_view(), name="client-media-upload"),
    path("<int:id>/", ClientMediaDeleteView.as_view(), name="client-media-delete"),
    path("uploads/", UploadFileView.as_view(), name="client-media-upload-alias"),
]
