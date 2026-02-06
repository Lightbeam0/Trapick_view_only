# In your view-only system: trapickapp/sync_api.py
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
from django.utils import timezone

from .models import Location, LocationDateGroup, TrafficAnalysis, VideoFile

logger = logging.getLogger(__name__)

# ==================== SIMPLE API KEY AUTH ====================
def require_sync_api_key(view_func):
    """Simple API key authentication"""
    from django.conf import settings
    from functools import wraps
    
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        api_key = request.headers.get('X-Sync-API-Key')
        expected_key = getattr(settings, 'SYNC_API_KEY', '')
        
        # For testing, if no key is set, allow all
        if not expected_key:
            return view_func(request, *args, **kwargs)
        
        if not api_key or api_key != expected_key:
            logger.warning(f"Invalid API key attempt from {request.META.get('REMOTE_ADDR')}")
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# ==================== MAIN SYNC VIEW ====================
@method_decorator([csrf_exempt, require_sync_api_key], name='dispatch')
class DataSyncAPI(View):
    """
    Endpoint: POST /api/sync-data/
    
    Receives pre-processed traffic data from local system and saves it to database.
    This replaces the video upload/ML processing pipeline.
    
    Expected JSON format:
    {
        "location_id": 1,
        "location_name": "Main Street Intersection",
        "date": "2024-01-15",
        "weather_condition": "clear",
        "analyses": [
            {
                "time_interval": "08:00-09:00",
                "vehicle_count": 150,
                "congestion_level": "medium",
                "avg_speed": 45.5,
                "weather_condition": "clear",
                "pedestrian_count": 12,
                "incident_count": 0,
                "vehicle_breakdown": {
                    "car": 100,
                    "truck": 20,
                    "motorcycle": 25,
                    "bus": 3,
                    "bicycle": 2,
                    "other": 0
                }
            }
        ]
    }
    """
    
    def post(self, request):
        try:
            # Parse JSON
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON format'}, status=400)
            
            logger.info(f"Sync request received for location: {data.get('location_id')}")
            
            # Process the data
            result = self._process_sync_data(data)
            
            return JsonResponse({
                'status': 'success',
                'message': f'Synced {result["analyses_processed"]} time intervals',
                'data': result
            })
            
        except KeyError as e:
            return JsonResponse({'error': f'Missing required field: {e}'}, status=400)
        except ValidationError as e:
            return JsonResponse({'error': f'Validation error: {e}'}, status=400)
        except Exception as e:
            logger.exception(f"Unexpected error in sync: {e}")
            return JsonResponse({'error': f'Processing error: {str(e)}'}, status=500)
    
    def _process_sync_data(self, data):
        """Process incoming sync data and save to database"""
        with transaction.atomic():
            # 1. Get or create location
            location, loc_created = Location.objects.get_or_create(
                id=data['location_id'],
                defaults={
                    'name': data.get('location_name', f"Location {data['location_id']}"),
                    'display_name': data.get('location_name', f"Location {data['location_id']}"),
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'description': data.get('description', ''),
                    'active': True
                }
            )
            
            # 2. Parse date
            date = parse_date(data['date'])
            if not date:
                raise ValidationError("Invalid date format. Use YYYY-MM-DD.")
            
            # 3. Get or create location-date group
            date_group, dg_created = LocationDateGroup.objects.get_or_create(
                location=location,
                date=date,
                defaults={
                    'weather_condition': data.get('weather_condition', 'unknown')
                }
            )
            
            # 4. Create a dummy video file for each analysis (optional)
            # This maintains compatibility with existing dashboard structure
            dummy_videos = []
            
            # 5. Process each time interval analysis
            analyses_processed = 0
            total_vehicles = 0
            
            for analysis_data in data.get('analyses', []):
                # Create dummy video for this time interval
                video = VideoFile.objects.create(
                    filename=f"synced_{location.id}_{date}_{analysis_data['time_interval'].replace(':', '')}.mp4",
                    file_path=f"synced_videos/synced_{location.id}_{date}_{analysis_data['time_interval'].replace(':', '')}.mp4",
                    video_date=date,
                    processing_status='completed',
                    processed=True,
                    location_date_group=date_group,
                    uploaded_at=timezone.now()
                )
                dummy_videos.append(video)
                
                # Extract vehicle breakdown
                breakdown = analysis_data.get('vehicle_breakdown', {})
                
                # Create traffic analysis
                analysis = TrafficAnalysis.objects.create(
                    video_file=video,
                    location=location,
                    total_vehicles=analysis_data.get('vehicle_count', 0),
                    congestion_level=analysis_data.get('congestion_level', 'low'),
                    avg_speed=analysis_data.get('avg_speed'),
                    
                    # Vehicle counts
                    car_count=breakdown.get('car', 0),
                    truck_count=breakdown.get('truck', 0),
                    motorcycle_count=breakdown.get('motorcycle', 0),
                    bus_count=breakdown.get('bus', 0),
                    bicycle_count=breakdown.get('bicycle', 0),
                    other_count=breakdown.get('other', 0),
                    
                    # Directional data (if provided)
                    directional_count=analysis_data.get('directional_count', 0),
                    congestion_percentage=analysis_data.get('congestion_percentage', 0),
                    
                    # Analysis metadata
                    processing_time_seconds=0,  # No processing time for synced data
                    analyzed_at=timezone.now(),
                    duration_seconds=3600,  # Assume 1-hour intervals
                    
                    # Store original sync data
                    analysis_data={
                        'synced': True,
                        'source': 'local_system',
                        'original_data': analysis_data,
                        'sync_timestamp': timezone.now().isoformat()
                    }
                )
                
                analyses_processed += 1
                total_vehicles += analysis.total_vehicles
            
            return {
                'location_id': location.id,
                'location_created': loc_created,
                'date_group_id': date_group.id,
                'date_group_created': dg_created,
                'analyses_processed': analyses_processed,
                'total_vehicles': total_vehicles,
                'timestamp': timezone.now().isoformat()
            }


# ==================== HEALTH CHECK ====================
@method_decorator(csrf_exempt, name='dispatch')
class SyncHealthCheck(View):
    """Health check endpoint"""
    
    def get(self, request):
        return JsonResponse({
            'status': 'healthy',
            'service': 'trapick-sync-api',
            'timestamp': timezone.now().isoformat()
        })