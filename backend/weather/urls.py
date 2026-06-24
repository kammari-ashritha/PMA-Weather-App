from django.urls import path
from . import views

urlpatterns = [
    path('auth/google/', views.google_auth, name='google-auth'),
    path('weather/current/', views.current_weather, name='current-weather'),
    path('weather/forecast/', views.forecast_weather, name='forecast-weather'),
    path('searches/', views.searches_list, name='searches-list'),
    path('searches/<str:search_id>/', views.search_detail, name='search-detail'),
    path('export/', views.export_data, name='export-data'),
]