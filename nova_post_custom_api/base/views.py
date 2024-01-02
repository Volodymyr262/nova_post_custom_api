from django.shortcuts import render, redirect, HttpResponse
import requests
from .forms import ParcelForm, ReturnRequestForm
from django.conf import settings  # Import settings
from django.http import JsonResponse
import googlemaps
from .moduls import search_settlements, search_settlement_streets


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


def check_return_possibility(request):
    # Your Nova Poshta API credentials
    api_key = settings.NOVA_POST_API_KEY
    api_url = 'https://api.novaposhta.ua/v2.0/json/'

    # Example data for checking return possibility
    data = {
        "apiKey": api_key,
        "modelName": "InternetDocument",
        "calledMethod": "checkPossibilityCreateReturn",
        "methodProperties": {
            "Number": "20450839412915"
        }
    }

    # Make a request to Nova Poshta API
    response = requests.post(api_url, json=data)
    api_response = response.json()

    # Check if the request was successful
    if 'success' in api_response and api_response['success']:
        # Check the possibility status in the response
        possibility_status = api_response.get('data', {}).get('Status', '')

        # You can customize the response based on your needs
        return JsonResponse({'success': True, 'possibility_status': possibility_status})
    else:
        # Handle the case where the request was not successful
        return JsonResponse({'success': False, 'message': 'Failed to check return possibility'})


def create_return_request(request):
    if request.method == 'POST':
        form = ReturnRequestForm(request.POST)
        api_key = settings.NOVA_POST_API_KEY
        if form.is_valid():
            tracking_number = form.cleaned_data['tracking_number']

            # Check if return is possible
            if not check_return_possibility(tracking_number):
                return JsonResponse({'success': False, 'message': 'Return is not possible for this parcel'})
            city_name = form.cleaned_data['recipient_settlement']
            street_name = form.cleaned_data['recipient_settlement_street']
            recipient_settlement = search_settlements(api_key, limit=1, city_name=city_name)
            recipient_settlement_street = search_settlement_streets(api_key, street_name=street_name,
                                                             settlement_ref=recipient_settlement, limit=1)
            print(recipient_settlement_street)
            print(recipient_settlement)

            return JsonResponse({'success': True, 'message': 'Return request created successfully'})

    else:
        form = ReturnRequestForm()

    return render(request, 'return_request_form.html', {'form': form})