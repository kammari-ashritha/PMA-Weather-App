from django.urls import path, include

urlpatterns = [
    path('https://pma-weather-app-kg8k.onrender.com/api/', include('weather.urls')),
]