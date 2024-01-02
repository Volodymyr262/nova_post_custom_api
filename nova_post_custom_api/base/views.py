from django.shortcuts import render, redirect, HttpResponse
import requests
from .forms import ParcelForm, ReturnRequestForm, RedirectRequestForm
from django.conf import settings  # Import settings
from django.http import JsonResponse
import googlemaps
from .moduls import get_return_reason_choices, get_return_subtype_choices
from .moduls import search_settlements, search_settlement_streets, create_return_request_api, check_return_possibility, \
    check_redirect_possibility, create_return_redirect_api, get_warehouses


def track_parcel(request):
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

            response = requests.post(api_url, json=data)
            api_response = response.json()

            if 'data' in api_response and api_response['data']:
                status_code = int(api_response['data'][0].get('StatusCode', ''))
                warehouse_recipient_address = api_response['data'][0].get('WarehouseRecipientAddress', '')
                warehouse_sender_address = api_response['data'][0].get('CitySender', '')
                status = api_response['data'][0].get('Status', '')
                print(status)
                # Use Google Maps Geocoding with language parameter
                gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

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
                        return render(request, 'parcel_tracker/result_without_address.html', {'status':status})
    else:
        form = ParcelForm()

    return render(request, 'parcel_tracker/track_parcel.html', {'form': form})


def create_return_request(request):
    if request.method == 'POST':
        form = ReturnRequestForm(request.POST)
        api_key = settings.NOVA_POST_API_KEY
        if form.is_valid():
            tracking_number = form.cleaned_data['tracking_number']

            # Check if return is possible
            if not check_return_possibility(request, tracking_number):
                return JsonResponse({'success': False, 'message': 'Return is not possible for this parcel'})
            api_response = create_return_request_api(api_key=api_key, form_data=form.data)
            print(api_response)
            return JsonResponse(api_response, safe=False, json_dumps_params={'ensure_ascii': False},
                                content_type='application/json;charset=utf-8')

    else:
        form = ReturnRequestForm()

    return render(request, 'return_request_form.html', {'form': form})


def create_redirect_response(request):
    if request.method == 'POST':
        form = RedirectRequestForm(request.POST)
        api_key = settings.NOVA_POST_API_KEY
        if form.is_valid():
            tracking_number = form.cleaned_data['IntDocNumber']
            # Check if redirect is possible
            if not check_redirect_possibility(request, tracking_number):
                return JsonResponse({'success': False, 'message': 'Return is not possible for this parcel'})
            api_response = create_return_redirect_api(api_key=api_key, form_data=form.data)
            return JsonResponse(api_response, safe=False, json_dumps_params={'ensure_ascii': False},
                                content_type='application/json;charset=utf-8')

    else:
        form = RedirectRequestForm()

    return render(request, 'return_redirect_form.html', {'form': form})