import requests
from django.conf import settings
from django.http import JsonResponse


def check_return_possibility(request, number):
    # Your Nova Poshta API credentials
    api_key = settings.NOVA_POST_API_KEY
    api_url = 'https://api.novaposhta.ua/v2.0/json/'

    # Example data for checking return possibility
    data = {
        "apiKey": api_key,
        "modelName": "InternetDocument",
        "calledMethod": "checkPossibilityCreateReturn",
        "methodProperties": {
            "Number": number
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


def check_redirect_possibility(request, number):
    # Your Nova Poshta API credentials
    api_key = settings.NOVA_POST_API_KEY
    api_url = 'https://api.novaposhta.ua/v2.0/json/'

    # Example data for checking return possibility
    data = {
        "apiKey": api_key,
        "modelName": "AdditionalServiceGeneral",
        "calledMethod": "checkPossibilityForRedirecting",
        "methodProperties": {
            "Number": number
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


def search_settlements(api_key, city_name, limit=1, page=1):
    api_url = 'https://api.novaposhta.ua/v2.0/json/'

    data = {
        "apiKey": api_key,
        "modelName": "Address",
        "calledMethod": "searchSettlements",
        "methodProperties": {
            "CityName": city_name,
            "Limit": str(limit),
            "Page": str(page)
        }
    }

    response = requests.post(api_url, json=data)
    api_response = response.json()

    if api_response['success']:
        refs = [address.get('Ref') for address in api_response['data'][0]['Addresses']]
        return ', '.join(refs)
    else:
        return None


def search_settlement_streets(api_key, street_name, settlement_ref, limit=1):
    api_url = 'https://api.novaposhta.ua/v2.0/json/'

    data = {
        "apiKey": api_key,
        "modelName": "Address",
        "calledMethod": "searchSettlementStreets",
        "methodProperties": {
            "StreetName": street_name,
            "SettlementRef": settlement_ref,
            "Limit": str(limit)
        }
    }

    response = requests.post(api_url, json=data)
    api_response = response.json()

    if 'data' in api_response and api_response['data']:
        streets = api_response['data'][0].get('Addresses', [])
        street_refs = [street.get('SettlementStreetRef') for street in streets]
        return ', '.join(street_refs)

    return None


import requests


def get_return_reasons(api_key):
    api_url = 'https://api.novaposhta.ua/v2.0/json/'
    data = {
        "apiKey": api_key,
        "modelName": "AdditionalService",
        "calledMethod": "getReturnReasons",
        "methodProperties": {}
    }
    response = requests.post(api_url, json=data)
    return response.json().get('data', [])


def get_return_reason_subtypes(api_key, reason_ref):
    api_url = 'https://api.novaposhta.ua/v2.0/json/'
    data = {
        "apiKey": api_key,
        "modelName": "AdditionalService",
        "calledMethod": "getReturnReasonsSubtypes",
        "methodProperties": {
            "ReasonRef": reason_ref
        }
    }
    response = requests.post(api_url, json=data)
    return response.json().get('data', [])


def get_return_reason_choices(api_key):
    reasons = get_return_reasons(api_key)
    return [(reason['Ref'], reason['Description']) for reason in reasons]


def get_return_subtype_choices(api_key, reason_ref):
    subtypes = get_return_reason_subtypes(api_key, reason_ref)
    return [(subtype['Ref'], subtype['Description']) for subtype in subtypes]


def create_return_request_api(api_key, form_data):
    api_url = 'https://api.novaposhta.ua/v2.0/json/'
    data = {
        "apiKey": api_key,
        "modelName": "AdditionalService",
        "calledMethod": "save",
        "methodProperties": {
            "IntDocNumber": form_data['tracking_number'],
            "PaymentMethod": form_data['payment_method'],
            "Reason": form_data['reason_ref'],
            "SubtypeReason": form_data['subtype_reason_ref'],
            "Note": form_data.get('note', ''),
            "OrderType": "orderCargoReturn",
            "RecipientSettlement": search_settlements(api_key, limit=1, city_name=form_data['recipient_settlement']),
            "RecipientSettlementStreet": search_settlement_streets(api_key, street_name=form_data['recipient_settlement_street'],
                                                             settlement_ref=search_settlements(api_key, limit=1, city_name=form_data['recipient_settlement']), limit=1),
            "BuildingNumber": form_data['building_number'],
            "NoteAddressRecipient": form_data['note_address_recipient']
        }
    }

    response = requests.post(api_url, json=data)
    return response.json()


def get_warehouses(api_key, city_name, warehouse_id=None, find_by_string=""):
    api_url = 'https://api.novaposhta.ua/v2.0/json/'

    data = {
        "apiKey": api_key,
        "modelName": "Address",
        "calledMethod": "getWarehouses",
        "methodProperties": {
            "FindByString": find_by_string,
            "CityName": city_name,
            "WarehouseId": warehouse_id,
            "Limit": 1
        }
    }

    response = requests.post(api_url, json=data)

    if response.json().get('data', []):
        data = response.json().get('data', [])
        return [warehouse.get('Ref') for warehouse in data][0]

    # Handle the case when the API request fails
    return None


def create_return_redirect_api(api_key, form_data):
    api_url = 'https://api.novaposhta.ua/v2.0/json/'
    city_name = form_data['RecipientSettlement']
    data = {
        "apiKey": api_key,
        "modelName": "AdditionalService",
        "calledMethod": "save",
        "methodProperties": {
            "IntDocNumber": form_data['IntDocNumber'],
            "PaymentMethod": form_data['PaymentMethod'],
            "Note": form_data['Note'],
            "OrderType": form_data["OrderType"],
            "RecipientContactName": form_data["RecipientContactName"],
            "RecipientPhone": form_data["RecipientPhone"],
            "Customer": form_data["Customer"],
            "PayerType": form_data.get('PayerType'),
            "ServiceType": form_data["ServiceType"],
            "RecipientSettlement": search_settlements(api_key, limit=1, city_name=form_data['RecipientSettlement']),
            "RecipientSettlementStreet": search_settlement_streets(
                api_key,
                street_name=form_data['RecipientSettlementStreet'],
                settlement_ref=search_settlements(api_key, limit=1, city_name=form_data['RecipientSettlement']),
                limit=1
            ),
            "BuildingNumber": form_data['BuildingNumber'],
            "NoteAddressRecipient": form_data['NoteAddressRecipient'],
            "RecipientWarehouse": get_warehouses(api_key, city_name=city_name
                                                   ,warehouse_id=form_data['RecipientWarehouseID'],find_by_string="")
        }
    }

    response = requests.post(api_url, json=data)
    return response.json()


def check_possibility_change_ew(api_key, int_doc_number):
    api_url = 'https://api.novaposhta.ua/v2.0/json/'

    data = {
        "apiKey": api_key,
        "modelName": "AdditionalService",
        "calledMethod": "CheckPossibilityChangeEW",
        "methodProperties": {
            "IntDocNumber": int_doc_number
        }
    }

    response = requests.post(api_url, json=data)
    result = response.json()

    # Отримуємо вартість поля "success"
    success_value = result.get('success', False)

    return success_value


def create_change_data_request_api(api_key, form_data):
    api_url = 'https://api.novaposhta.ua/v2.0/json/'

    data = {
        "apiKey": api_key,
        "modelName": "AdditionalService",
        "calledMethod": "save",
        "methodProperties": {
            "IntDocNumber": form_data['IntDocNumber'],
            "PaymentMethod": form_data['PaymentMethod'],
            "OrderType": form_data["OrderType"],
            "SenderContactName": form_data["SenderContactName"],
            "SenderPhone": form_data["SenderPhone"],
            #"Recipient": form_data.get("Recipient", ''),
            "RecipientContactName": form_data.get("RecipientContactName", ''),
            "RecipientPhone": form_data.get("RecipientPhone", ''),
            "PayerType": form_data['PayerType'],
        }
    }

    response = requests.post(api_url, json=data)
    return response.json()