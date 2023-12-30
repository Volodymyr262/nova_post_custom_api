from django.urls import path
from . import views


urlpatterns = [
    path('', views.track_parcel, name='track_parcel'),
]
