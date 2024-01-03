from django.shortcuts import render, redirect
import requests
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView
from .forms import ParcelForm, ReturnRequestForm, RedirectRequestForm, ChangeDataRequestForm, CustomUserCreationForm
from django.conf import settings  # Import settings
from django.http import JsonResponse
import googlemaps
from django.contrib import messages
from django.urls import reverse_lazy
from .moduls import create_return_request_api, check_return_possibility, \
    check_redirect_possibility, create_return_redirect_api, check_possibility_change_ew, create_change_data_request_api
from django.http import HttpResponseServerError
from googlemaps import Client as GoogleMapsClient
from googlemaps import exceptions as gmaps_exceptions


class CustomLoginView(LoginView):
    template_name = 'login/login.html'
    success_url = reverse_lazy('')


class CustomRegisterView(CreateView):
    template_name = 'login/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('track_parcel')


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')


def track_parcel(request):
    if not request.user.is_authenticated:
        messages.error(request, 'You need to log in first.')
        return redirect('login')

    if request.method == 'POST':
        form = ParcelForm(request.POST)
        if form.is_valid():
            parcel_number = form.cleaned_data['parcel_number']

            # Fetch address details from Nova Poshta API
            api_url = 'https://api.novaposhta.ua/v2.0/json/getStatusDocuments'
            api_key = settings.NOVA_POST_API_KEY

            data = {
                "apiKey": api_key,
                "modelName": "TrackingDocument",
                "calledMethod": "getStatusDocuments",
                "methodProperties": {
                    "Documents": [
                        {
                            "DocumentNumber": parcel_number,
                            "Phone": "380600000000"
                        }
                    ]
                }
            }

            status_codes_without_address = [2, 3, 102, 105]
            status_codes_with_sender_address = [1, 12, 112, 111]
            status_codes_with_recipient_address = [41, 7, 8, 10, 101, 9, 11]
            status_codes_on_the_way = [5, 6, 41, 4]

            try:
                response = requests.post(api_url, json=data)
                response.raise_for_status()

                api_response = response.json()

                if 'data' in api_response and api_response['data']:
                    status_code = int(api_response['data'][0].get('StatusCode', ''))
                    warehouse_recipient_address = api_response['data'][0].get('WarehouseRecipientAddress', '')
                    warehouse_sender_address = api_response['data'][0].get('CitySender', '')
                    status = api_response['data'][0].get('Status', '')

                    # Use Google Maps Geocoding with language parameter
                    gmaps = GoogleMapsClient(key=settings.GOOGLE_MAPS_API_KEY)

                    # Geocode recipient and sender addresses
                    geocode_recipient = gmaps.geocode(warehouse_recipient_address, language='uk')
                    geocode_sender = gmaps.geocode(warehouse_sender_address, language='uk')

                    if geocode_recipient and geocode_sender:
                        location_recipient = geocode_recipient[0]['geometry']['location']
                        location_sender = geocode_sender[0]['geometry']['location']

                        if status_code in status_codes_on_the_way:
                            return render(request, 'parcel_tracker/result_on_the_way.html', {
                                'warehouse_recipient_address': warehouse_recipient_address,
                                'warehouse_sender_address': warehouse_sender_address,
                                'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
                                'location_recipient': location_recipient,
                                'location_sender': location_sender,
                                'status': status,
                            })

                        elif status_code in status_codes_with_recipient_address:
                            return render(request, 'parcel_tracker/result.html', {
                                'address': warehouse_recipient_address,
                                'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
                                'location': location_recipient,
                                'status': status  # Include status in the render context
                            })

                        elif status_code in status_codes_with_sender_address:
                            return render(request, 'parcel_tracker/result.html', {
                                'address': warehouse_sender_address,
                                'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
                                'location': location_recipient,
                                'status': status  # Include status in the render context
                            })

                        elif status_code in status_codes_without_address:
                            return render(request, 'parcel_tracker/result_without_address.html', {'status': status})
                else:
                    return JsonResponse('ss')
            except gmaps_exceptions.HTTPError as e:
                # Handle Google Maps API HTTPError
                messages.error(request, "Error fetching data from Google Maps API. Please try again later.")
                return HttpResponseServerError("Error fetching data from Google Maps API. Please try again later.")

            except Exception as e:
                # Handle other exceptions if needed
                messages.error(request, "An unexpected error occurred. Please try again later.")
                return HttpResponseServerError("Ви ввели неправильний номер посилки.")

    else:
        form = ParcelForm()

    return render(request, 'parcel_tracker/track_parcel.html', {'form': form})


def create_return_request(request):
    if not request.user.is_authenticated:
        messages.error(request, 'You need to log in first.')
        return redirect('login')
    if request.method == 'POST':
        form = ReturnRequestForm(request.POST)
        api_key = settings.NOVA_POST_API_KEY
        if form.is_valid():
            tracking_number = form.cleaned_data['tracking_number']

            # Check if return is possible
            if not check_return_possibility(request, tracking_number):
                return JsonResponse({'success': False, 'message': 'Return is not possible for this parcel'})
            api_response = create_return_request_api(api_key=api_key, form_data=form.data)
            if api_response.get('success', False):
                return render(request, 'success_template.html', {'data': api_response['data'][0]})
            else:
                return render(request, 'return_request_form.html',
                              {'form': form, 'success': False, 'errors': api_response['errors']})

    else:
        form = ReturnRequestForm()

    return render(request, 'return_request_form.html', {'form': form})


def create_redirect_response(request):
    if not request.user.is_authenticated:
        messages.error(request, 'You need to log in first.')
        return redirect('login')

    if request.method == 'POST':
        form = RedirectRequestForm(request.POST)
        api_key = settings.NOVA_POST_API_KEY

        if form.is_valid():
            tracking_number = form.cleaned_data['IntDocNumber']

            # Check if redirect is possible
            if not check_redirect_possibility(request, tracking_number):
                messages.error(request, 'Return is not possible for this parcel')
                return render(request, 'return_redirect_form.html', {'form': form, 'success': False})

            api_response = create_return_redirect_api(api_key=api_key, form_data=form.data)

            if api_response.get('success', False):
                return render(request, 'success_template.html', {'data': api_response['data'][0]})
            else:
                return render(request, 'return_redirect_form.html', {'form': form, 'success': False, 'errors': api_response['errors']})

    else:
        form = RedirectRequestForm()

    return render(request, 'return_redirect_form.html', {'form': form, 'success': None})


def create_data_change_response(request):
    if not request.user.is_authenticated:
        messages.error(request, 'You need to log in first.')
        return redirect('login')
    if request.method == 'POST':
        form = ChangeDataRequestForm(request.POST)
        api_key = settings.NOVA_POST_API_KEY
        if form.is_valid():
            tracking_number = form.cleaned_data['IntDocNumber']
            api_response = create_change_data_request_api(api_key, form.data)
            if api_response.get('success', False):
                return render(request, 'success_template.html', {'data': api_response['data'][0]})
            else:
                return render(request, 'data_change_form.html',
                              {'form': form, 'success': False, 'errors': api_response['errors']})
    else:
        form = ChangeDataRequestForm()

    return render(request, 'data_change_form.html', {'form':form})