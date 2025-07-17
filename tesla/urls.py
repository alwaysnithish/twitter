from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Main page - handles GET for rendering the form and POST for getting video qualities
    path('', views.TwitterVideoDownloader.as_view(), name='index'),
    
    # CSRF token endpoint
    path('get-csrf-token/', views.get_csrf_token, name='get_csrf_token'),
    
    # Download endpoint - handles POST requests to stream video downloads
    path('download-video-stream/', views.download_video_stream, name='download_video_stream'),
    
    # Cookies status endpoint - checks if cookies file exists
    path('cookies-status/', views.cookies_status, name='cookies_status'),
    
    # Video info endpoint - gets additional video metadata
    path('video-info/', views.video_info, name='video_info'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

