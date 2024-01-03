# Імпорт необхідних модулів і класів
from django.shortcuts import render, redirect
import requests
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.edit import CreateView
from .forms import ParcelForm, ReturnRequestForm, RedirectRequestForm, ChangeDataRequestForm, CustomUserCreationForm
from django.conf import settings  # Import settings
from django.http import JsonResponse
from django.contrib.auth import login
import googlemaps
from django.contrib import messages
from django.urls import reverse_lazy
from .moduls import create_return_request_api, check_return_possibility, \
    check_redirect_possibility, create_return_redirect_api, create_change_data_request_api
from django.http import HttpResponseServerError
from googlemaps import Client as GoogleMapsClient
from googlemaps import exceptions as gmaps_exceptions


# Клас для користувача: сторінка входу
class CustomLoginView(LoginView):
    template_name = 'login/login.html'
    success_url = reverse_lazy('')


# Клас для користувача: сторінка реєстрації
class CustomRegisterView(CreateView):
    template_name = 'login/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('track_parcel')

    # Перевизначення методу form_valid для автоматичного входу користувача після реєстрації
    def form_valid(self, form):
        # Call the parent class's form_valid method to save the user
        response = super().form_valid(form)

        # Log in the user after successful registration
        login(self.request, self.object)

        return response


# Клас для користувача: вихід з акаунту
class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')


# Відслідковування посилки
def track_parcel(request):
    # Перевірка, чи користувач автентифікований
    if not request.user.is_authenticated:
        messages.error(request, 'Увійдіть в свій акаунт спочатку.')
        return redirect('login')

    if request.method == 'POST':
        # Обробка відправленої форми відстеження посилки
        form = ParcelForm(request.POST)
        if form.is_valid():
            parcel_number = form.cleaned_data['parcel_number']

            # Отримання деталей адреси з API Nova Poshta
            api_url = 'https://api.novaposhta.ua/v2.0/json/getStatusDocuments'
            api_key = settings.NOVA_POST_API_KEY
            # Створення даних для запиту API
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
            # Визначення кодів статусу для різних сценаріїв
            status_codes_without_address = [2, 3, 102, 105]
            status_codes_with_sender_address = [1, 12, 112, 111]
            status_codes_with_recipient_address = [41, 7, 8, 10, 101, 9, 11]
            status_codes_on_the_way = [5, 6, 41, 4]

            try:
                # Виклик API Nova Poshta
                response = requests.post(api_url, json=data)
                response.raise_for_status()
                # Обробка відповіді API
                api_response = response.json()

                if 'data' in api_response and api_response['data']:
                    status_code = int(api_response['data'][0].get('StatusCode', ''))
                    warehouse_recipient_address = api_response['data'][0].get('WarehouseRecipientAddress', '')
                    warehouse_sender_address = api_response['data'][0].get('CitySender', '')
                    status = api_response['data'][0].get('Status', '')

                    # Використання Google Maps Geocoding із параметром мови
                    gmaps = GoogleMapsClient(key=settings.GOOGLE_MAPS_API_KEY)

                    # Геокодування адреси отримувача та відправника
                    geocode_recipient = gmaps.geocode(warehouse_recipient_address, language='uk')
                    geocode_sender = gmaps.geocode(warehouse_sender_address, language='uk')

                    if geocode_recipient and geocode_sender:
                        location_recipient = geocode_recipient[0]['geometry']['location']
                        location_sender = geocode_sender[0]['geometry']['location']
                        # Відображення різних шаблонів на основі кодів статусу
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
                # Обробка помилки HTTP від Google Maps API
                messages.error(request, "Error fetching data from Google Maps API. Please try again later.")
                return HttpResponseServerError("Error fetching data from Google Maps API. Please try again later.")

            except Exception as e:
                # Обробка інших винятків за потреби
                messages.error(request, "An unexpected error occurred. Please try again later.")
                return HttpResponseServerError("Ви ввели неправильний номер посилки.")

    else:
        form = ParcelForm()

    return render(request, 'parcel_tracker/track_parcel.html', {'form': form})


# View для створення запиту на повернення посилки
def create_return_request(request):
    # Перевірка, чи користувач автентифікований
    if not request.user.is_authenticated:
        messages.error(request, 'Увійдіть в свій акаунт спочатку.')
        return redirect('login')
    if request.method == 'POST':
        # Обробка відправленої форми для запиту на повернення
        form = ReturnRequestForm(request.POST)
        api_key = settings.NOVA_POST_API_KEY
        if form.is_valid():
            tracking_number = form.cleaned_data['tracking_number']

            # Перевірка можливості повернення
            if not check_return_possibility(request, tracking_number):
                return JsonResponse({'success': False, 'message': 'Return is not possible for this parcel'})
            # Створення API-запиту на повернення
            api_response = create_return_request_api(api_key=api_key, form_data=form.data)
            if api_response.get('success', False):
                return render(request, 'success_template_return.html', {'data': api_response['data'][0]})
            else:
                return render(request, 'return_request_form.html',
                              {'form': form, 'success': False, 'errors': api_response['errors']})

    else:
        form = ReturnRequestForm()

    return render(request, 'return_request_form.html', {'form': form})


# view для створення запиту на перенаправлення
def create_redirect_response(request):
    # Перевірка, чи користувач автентифікований
    if not request.user.is_authenticated:
        messages.error(request, 'Увійдіть в свій акаунт спочатку.')
        return redirect('login')

    if request.method == 'POST':
        # Обробка відправленої форми для запиту на перенаправлення
        form = RedirectRequestForm(request.POST)
        api_key = settings.NOVA_POST_API_KEY

        if form.is_valid():
            tracking_number = form.cleaned_data['IntDocNumber']

            # Перевірка можливості перенаправлення
            if not check_redirect_possibility(request, tracking_number):
                messages.error(request, 'Return is not possible for this parcel')
                return render(request, 'return_redirect_form.html', {'form': form, 'success': False})
            # Створення API-запиту на перенаправлення
            api_response = create_return_redirect_api(api_key=api_key, form_data=form.data)

            if api_response.get('success', False):
                return render(request, 'success_template_redirect.html', {'data': api_response['data'][0]})
            else:
                return render(request, 'return_redirect_form.html', {'form': form, 'success': False, 'errors': api_response['errors']})

    else:
        form = RedirectRequestForm()

    return render(request, 'return_redirect_form.html', {'form': form, 'success': None})


# view для створення запиту на зміну даних
def create_data_change_response(request):
    # Перевірка, чи користувач автентифікований
    if not request.user.is_authenticated:
        messages.error(request, 'Увійдіть в свій акаунт спочатку.')
        return redirect('login')
    if request.method == 'POST':
        # Обробка відправленої форми для запиту на зміну даних
        form = ChangeDataRequestForm(request.POST)
        api_key = settings.NOVA_POST_API_KEY
        if form.is_valid():
            tracking_number = form.cleaned_data['IntDocNumber']
            api_response = create_change_data_request_api(api_key, form.data)
            if api_response.get('success', False):
                return render(request, 'success_template_data_change.html', {'data': api_response['data'][0]})
            else:
                return render(request, 'data_change_form.html',
                              {'form': form, 'success': False, 'errors': api_response['errors']})
    else:
        form = ChangeDataRequestForm()

    return render(request, 'data_change_form.html', {'form':form})