from django.urls import path
from . import views


urlpatterns = [
    path('', views.track_parcel, name='track_parcel'),
    path('data_change/', views.create_data_change_response, name='data_change'),
    path('return/', views.create_return_request, name='return_service'),
    path('redirect/', views.create_redirect_response, name='redirect_service')

]
