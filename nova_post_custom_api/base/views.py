from django.shortcuts import render, redirect
import requests
from .forms import ParcelForm


def track_parcel(request):
    if request.method == 'POST':
        form = ParcelForm(request.POST)
        if form.is_valid():
            parcel_number = form.cleaned_data['parcel_number']

            # Send GET request to the API
            api_url = 'https://api.novaposhta.ua/v2.0/json/getStatusDocuments'
            api_key = 'dbdc46b2bf4d3cbb63ad4235d7e30c78'

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

            response = requests.post(api_url, json=data)
            api_response = response.json()

            # Process the API response as needed

            return render(request, 'parcel_tracker/result.html', {'api_response': api_response})

    else:
        form = ParcelForm()

    return render(request, 'parcel_tracker/parcel_tracker.html', {'form': form})