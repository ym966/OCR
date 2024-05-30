from django.urls import path
from .views import FileUploadView, CheckStatusView, DownloadFileView

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    
    path('status/<str:pk>/', CheckStatusView.as_view(), name='check-status'),
    path('download/<str:pk>/', DownloadFileView.as_view(), name='download-file'),
]
print(urlpatterns)