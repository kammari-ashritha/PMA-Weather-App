import requests
import csv
import json
import io
from datetime import datetime
from bson import ObjectId
from django.conf import settings
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .db import get_collection

OWM_BASE = 'https://api.openweathermap.org/data/2.5'


def fetch_from_owm(endpoint, location=None, lat=None, lon=None):
    """Fetch data from OpenWeatherMap API"""
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        raise ValueError('OpenWeatherMap API key not set in .env file')

    params = {'appid': api_key, 'units': 'metric'}
    if lat and lon:
        params['lat'] = lat
        params['lon'] = lon
    elif location:
        params['q'] = location
    else:
        raise ValueError('Provide either location name or lat/lon coordinates')

    res = requests.get(f'{OWM_BASE}/{endpoint}', params=params, timeout=10)
    res.raise_for_status()
    return res.json()


@api_view(['GET'])
def current_weather(request):
    """GET /api/weather/current/?location=London OR ?lat=51.5&lon=-0.1"""
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
            return Response({'error': 'Invalid API key. Check your .env file.'}, status=401)
        return Response({'error': 'Weather service unavailable. Try again later.'}, status=503)
    except ValueError as e:
        return Response({'error': str(e)}, status=400)
    except Exception as e:
        return Response({'error': f'Unexpected error: {str(e)}'}, status=500)


@api_view(['GET'])
def forecast_weather(request):
    """GET /api/weather/forecast/?location=London"""
    location = request.GET.get('location')
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    try:
        data = fetch_from_owm('forecast', location=location, lat=lat, lon=lon)
        return Response(data)
    except requests.HTTPError as e:
        code = e.response.status_code
        if code == 404:
            return Response({'error': 'City not found for forecast.'}, status=404)
        return Response({'error': 'Forecast service unavailable.'}, status=503)
    except ValueError as e:
        return Response({'error': str(e)}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET', 'POST'])
def searches_list(request):
    """
    GET  /api/searches/ - READ all saved searches
    POST /api/searches/ - CREATE a new saved search
    """
    col = get_collection('searches')

    if request.method == 'GET':
        searches = list(col.find().sort('created_at', -1))
        for s in searches:
            s['_id'] = str(s['_id'])
        return Response(searches)

    if request.method == 'POST':
        data = request.data
        location = (data.get('location') or '').strip()
        date_start = data.get('date_range_start', '')
        date_end = data.get('date_range_end', '')

        # Validate inputs
        if not location:
            return Response({'error': 'Location is required'}, status=400)
        if not date_start or not date_end:
            return Response({'error': 'Both start and end dates are required'}, status=400)
        try:
            start = datetime.strptime(date_start, '%Y-%m-%d')
            end = datetime.strptime(date_end, '%Y-%m-%d')
            if end < start:
                return Response({'error': 'End date must be after or equal to start date'}, status=400)
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

        doc = {
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
    """
    PUT    /api/searches/<id>/ - UPDATE a saved search
    DELETE /api/searches/<id>/ - DELETE a saved search
    """
    col = get_collection('searches')
    try:
        obj_id = ObjectId(search_id)
    except Exception:
        return Response({'error': 'Invalid search ID format'}, status=400)

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
            return Response({'error': 'No fields to update'}, status=400)

        update_fields['updated_at'] = datetime.utcnow().isoformat()
        result = col.update_one({'_id': obj_id}, {'$set': update_fields})

        if result.matched_count == 0:
            return Response({'error': 'Search record not found'}, status=404)

        updated = col.find_one({'_id': obj_id})
        updated['_id'] = str(updated['_id'])
        return Response(updated)

    if request.method == 'DELETE':
        result = col.delete_one({'_id': obj_id})
        if result.deleted_count == 0:
            return Response({'error': 'Search record not found'}, status=404)
        return Response({'message': 'Deleted successfully'}, status=200)


@api_view(['GET'])
def export_data(request):
    """
    GET /api/export/?format=json  - Export all searches as JSON
    GET /api/export/?format=csv   - Export all searches as CSV
    """
    fmt = request.GET.get('format', 'json').lower()
    col = get_collection('searches')
    searches = list(col.find().sort('created_at', -1))

    # Prepare flat data for export
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
        return HttpResponse(
            content,
            content_type='application/json',
            headers={'Content-Disposition': 'attachment; filename="weather-searches.json"'}
        )

    elif fmt == 'csv':
        output = io.StringIO()
        if flat_data:
            writer = csv.DictWriter(output, fieldnames=flat_data[0].keys())
            writer.writeheader()
            writer.writerows(flat_data)
        return HttpResponse(
            output.getvalue(),
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="weather-searches.csv"'}
        )
    else:
        return Response({'error': 'Unsupported format. Use json or csv.'}, status=400)