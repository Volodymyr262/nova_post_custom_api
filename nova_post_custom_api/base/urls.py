from django.urls import path
from . import views


urlpatterns = [
    path('', views.track_parcel, name='track_parcel'),
    path('return-reason/', views.track_parcel,name='return-reason'),
    path('return/', views.create_return_request, name='return_service'),
    path('redirect/', views.create_redirect_response, name='redirect_service')
]
