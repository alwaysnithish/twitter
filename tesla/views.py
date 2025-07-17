import os
import json
import yt_dlp
import requests
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views import View
from urllib.parse import urlparse
from django.middleware.csrf import get_token
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def get_csrf_token(request):
    return JsonResponse({'csrf_token': get_token(request)})

# Your other existing views...
def your_existing_view(request):
    # your existing code
    pass

class TwitterVideoDownloader(View):
    """
    Handles the main page rendering and fetching video quality options.
    """
    def get(self, request):
        # Changed to match your HTML file name
        return render(request, 'home.html')

    @method_decorator(csrf_exempt)
    def post(self, request):
        try:
            data = json.loads(request.body)
            url = data.get('url', '').strip()

            if not url or not self._is_valid_twitter_url(url):
                return JsonResponse({'error': 'Please provide a valid Twitter/X URL'}, status=400)

            qualities = self._get_video_qualities(url)

            if not qualities:
                return JsonResponse({'error': 'No video found or unable to extract information.'}, status=404)

            return JsonResponse({
                'success': True,
                'qualities': qualities
            })
        except Exception as e:
            print(f"Error in TwitterVideoDownloader POST: {e}")
            return JsonResponse({'error': 'An unexpected server error occurred.'}, status=500)

    def _is_valid_twitter_url(self, url):
        parsed = urlparse(url)
        return parsed.netloc in ['twitter.com', 'x.com', 'www.twitter.com', 'www.x.com']

    def _get_video_qualities(self, url):
        cookies_file = os.path.join(settings.BASE_DIR, 'x.txt')
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'cookiefile': cookies_file if os.path.exists(cookies_file) else None,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            video_formats = []
            seen_heights = set()
            
            sorted_formats = sorted(info.get('formats', []), key=lambda f: f.get('height', 0), reverse=True)

            for fmt in sorted_formats:
                if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none' and fmt.get('ext') == 'mp4':
                    height = fmt.get('height')
                    if height and height not in seen_heights:
                        video_formats.append({
                            'quality': f"{height}p",
                            'height': height,
                            'width': fmt.get('width', 0),
                            'filesize': fmt.get('filesize_approx', 0),
                            'fps': fmt.get('fps', 0),
                            'ext': fmt.get('ext', 'mp4'),
                            'direct_url': fmt['url']
                        })
                        seen_heights.add(height)
                
                if len(video_formats) >= 3:
                    break
            
            return video_formats

@csrf_exempt
@require_http_methods(["POST"])
def download_video_stream(request):
    """
    Receives a direct video URL and streams it to the user.
    """
    try:
        data = json.loads(request.body)
        direct_url = data.get('direct_url')
        quality = data.get('quality', 'video')

        if not direct_url:
            return JsonResponse({'error': 'Missing direct video URL.'}, status=400)

        response = requests.get(direct_url, stream=True, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', 'video/mp4')
        filename = f"twitter_video_{quality}.mp4"

        streaming_response = StreamingHttpResponse(
            response.iter_content(chunk_size=8192),
            content_type=content_type
        )
        
        streaming_response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return streaming_response

    except requests.exceptions.RequestException as e:
        print(f"Error streaming video: {e}")
        return HttpResponseServerError("<h1>Error: Could not retrieve video for download.</h1>")
    except Exception as e:
        print(f"An unexpected error occurred during download stream: {e}")
        return JsonResponse({'error': f'Download failed: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def cookies_status(request):
    """
    Check if cookies file exists and return status.
    """
    try:
        cookies_file = os.path.join(settings.BASE_DIR, 'x.txt')
        cookies_exists = os.path.exists(cookies_file)
        cookies_size = 0
        
        if cookies_exists:
            cookies_size = os.path.getsize(cookies_file)
        
        return JsonResponse({
            'cookies_exists': cookies_exists,
            'cookies_size': cookies_size
        })
    except Exception as e:
        print(f"Error checking cookies status: {e}")
        return JsonResponse({
            'cookies_exists': False,
            'cookies_size': 0
        })

@csrf_exempt
@require_http_methods(["GET"])
def video_info(request):
    """
    Get additional video information for display.
    """
    try:
        url = request.GET.get('url', '').strip()
        
        if not url:
            return JsonResponse({'error': 'URL is required'}, status=400)

        cookies_file = os.path.join(settings.BASE_DIR, 'x.txt')
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'cookiefile': cookies_file if os.path.exists(cookies_file) else None,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return JsonResponse({
                'uploader': info.get('uploader', 'Unknown'),
                'duration': info.get('duration', 0),
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0),
                'title': info.get('title', 'Unknown'),
                'description': info.get('description', ''),
                'upload_date': info.get('upload_date', ''),
                'thumbnail': info.get('thumbnail', '')
            })
    except Exception as e:
        print(f"Error getting video info: {e}")
        return JsonResponse({'error': 'Failed to get video info'}, status=500)