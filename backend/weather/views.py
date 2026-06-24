import requests
import csv
import json
import io
from datetime import datetime
from bson import ObjectId
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .db import get_collection

OWM_BASE = 'https://api.openweathermap.org/data/2.5'


# ── HELPER: Get user from request header ──────────────────────────────────────

def get_user_id(request):
    """Extract user_id from X-User-Id header"""
    return request.META.get('HTTP_X_USER_ID', None)


# ── AUTH ──────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def google_auth(request):
    """
    POST /api/auth/google/
    Body: { "credential": "<google_id_token>" }
    Returns: { "user_id", "email", "name", "picture" }
    """
    credential = request.data.get('credential')
    if not credential:
        return Response({'error': 'No credential provided'}, status=400)

    try:
        client_id = settings.GOOGLE_CLIENT_ID
        id_info = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            client_id,
            clock_skew_in_seconds=10
        )

        user_data = {
            'user_id': id_info['sub'],
            'email': id_info['email'],
            'name': id_info.get('name', ''),
            'picture': id_info.get('picture', ''),
        }

        # Save or update user in MongoDB
        users_col = get_collection('users')
        users_col.update_one(
            {'user_id': id_info['sub']},
            {'$set': {**user_data, 'last_login': datetime.utcnow().isoformat()}},
            upsert=True
        )

        return Response(user_data)

    except ValueError as e:
        return Response({'error': f'Invalid token: {str(e)}'}, status=401)
    except Exception as e:
        return Response({'error': f'Auth failed: {str(e)}'}, status=500)


# ── WEATHER ───────────────────────────────────────────────────────────────────

def fetch_from_owm(endpoint, location=None, lat=None, lon=None):
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        raise ValueError('OpenWeatherMap API key not configured')

    params = {'appid': api_key, 'units': 'metric'}
    if lat and lon:
        params['lat'] = lat
        params['lon'] = lon
    elif location:
        params['q'] = location
    else:
        raise ValueError('Provide location or coordinates')

    res = requests.get(f'{OWM_BASE}/{endpoint}', params=params, timeout=10)
    res.raise_for_status()
    return res.json()


@api_view(['GET'])
def current_weather(request):
    location = request.GET.get('location')
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    try:
        data = fetch_from_owm('weather', location=location, lat=lat, lon=lon)
        return Response(data)
    except requests.HTTPError as e:
        code = e.response.status_code
        if code == 404:
            return Response({'error': 'City not found. Check spelling and try again.'}, status=404)
        if code == 401:
            return Response({'error': 'Invalid API key.'}, status=401)
        return Response({'error': 'Weather service unavailable.'}, status=503)
    except ValueError as e:
        return Response({'error': str(e)}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def forecast_weather(request):
    location = request.GET.get('location')
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    try:
        data = fetch_from_owm('forecast', location=location, lat=lat, lon=lon)
        return Response(data)
    except requests.HTTPError as e:
        code = e.response.status_code
        if code == 404:
            return Response({'error': 'City not found.'}, status=404)
        return Response({'error': 'Forecast unavailable.'}, status=503)
    except ValueError as e:
        return Response({'error': str(e)}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# ── SEARCHES (CRUD) ───────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def searches_list(request):
    col = get_collection('searches')
    user_id = get_user_id(request)

    if request.method == 'GET':
        # Filter by user if logged in, else return empty
        query = {'user_id': user_id} if user_id else {'user_id': 'anonymous'}
        searches = list(col.find(query).sort('created_at', -1))
        for s in searches:
            s['_id'] = str(s['_id'])
        return Response(searches)

    if request.method == 'POST':
        data = request.data
        location = (data.get('location') or '').strip()
        date_start = data.get('date_range_start', '')
        date_end = data.get('date_range_end', '')

        if not location:
            return Response({'error': 'Location is required'}, status=400)
        if not date_start or not date_end:
            return Response({'error': 'Both dates are required'}, status=400)
        try:
            start = datetime.strptime(date_start, '%Y-%m-%d')
            end = datetime.strptime(date_end, '%Y-%m-%d')
            if end < start:
                return Response({'error': 'End date must be after start date'}, status=400)
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=400)

        doc = {
            'user_id': user_id or 'anonymous',
            'location': location,
            'date_range_start': date_start,
            'date_range_end': date_end,
            'weather_data': data.get('weather_data', {}),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
        }
        result = col.insert_one(doc)
        doc['_id'] = str(result.inserted_id)
        return Response(doc, status=201)


@api_view(['PUT', 'DELETE'])
def search_detail(request, search_id):
    col = get_collection('searches')
    user_id = get_user_id(request)

    try:
        obj_id = ObjectId(search_id)
    except Exception:
        return Response({'error': 'Invalid ID'}, status=400)

    if request.method == 'PUT':
        update_fields = {}
        if 'location' in request.data:
            loc = request.data['location'].strip()
            if not loc:
                return Response({'error': 'Location cannot be empty'}, status=400)
            update_fields['location'] = loc
        if 'date_range_start' in request.data:
            update_fields['date_range_start'] = request.data['date_range_start']
        if 'date_range_end' in request.data:
            update_fields['date_range_end'] = request.data['date_range_end']

        if not update_fields:
            return Response({'error': 'Nothing to update'}, status=400)

        update_fields['updated_at'] = datetime.utcnow().isoformat()

        # Only update if belongs to this user
        query = {'_id': obj_id}
        if user_id:
            query['user_id'] = user_id

        result = col.update_one(query, {'$set': update_fields})
        if result.matched_count == 0:
            return Response({'error': 'Record not found'}, status=404)

        updated = col.find_one({'_id': obj_id})
        updated['_id'] = str(updated['_id'])
        return Response(updated)

    if request.method == 'DELETE':
        query = {'_id': obj_id}
        if user_id:
            query['user_id'] = user_id

        result = col.delete_one(query)
        if result.deleted_count == 0:
            return Response({'error': 'Record not found'}, status=404)
        return Response({'message': 'Deleted'}, status=200)


# ── EXPORT ────────────────────────────────────────────────────────────────────

@csrf_exempt
def export_data(request):
    fmt = request.GET.get('format', 'json').lower()
    user_id = request.META.get('HTTP_X_USER_ID', None)
    col = get_collection('searches')

    query = {'user_id': user_id} if user_id else {}
    searches = list(col.find(query).sort('created_at', -1))

    flat_data = []
    for s in searches:
        s['_id'] = str(s['_id'])
        flat_data.append({
            'id': s['_id'],
            'location': s.get('location', ''),
            'date_range_start': s.get('date_range_start', ''),
            'date_range_end': s.get('date_range_end', ''),
            'temperature_c': round(s.get('weather_data', {}).get('main', {}).get('temp', 0), 1),
            'condition': s.get('weather_data', {}).get('weather', [{}])[0].get('description', ''),
            'humidity_pct': s.get('weather_data', {}).get('main', {}).get('humidity', ''),
            'wind_speed_ms': s.get('weather_data', {}).get('wind', {}).get('speed', ''),
            'country': s.get('weather_data', {}).get('sys', {}).get('country', ''),
            'saved_at': s.get('created_at', ''),
        })

    if fmt == 'json':
        content = json.dumps(flat_data, indent=2, default=str)
        response = HttpResponse(content, content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="weather-searches.json"'
        return response

    elif fmt == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="weather-searches.csv"'
        if flat_data:
            writer = csv.DictWriter(response, fieldnames=flat_data[0].keys())
            writer.writeheader()
            writer.writerows(flat_data)
        else:
            response.write("No data\n")
        return response

    return HttpResponse(
        json.dumps({'error': 'Use json or csv'}),
        content_type='application/json',
        status=400
    )