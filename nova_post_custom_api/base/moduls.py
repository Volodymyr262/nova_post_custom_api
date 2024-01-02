import requests


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
