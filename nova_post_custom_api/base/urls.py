from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('', views.track_parcel, name='track_parcel'),
    path('data_change/', views.create_data_change_response, name='data_change'),
    path('return/', views.create_return_request, name='return_service'),
    path('redirect/', views.create_redirect_response, name='redirect_service'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.CustomRegisterView.as_view(), name='register'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout')

]
