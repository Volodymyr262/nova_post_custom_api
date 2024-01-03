# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Parcel
from .moduls import get_return_reason_choices, get_return_subtype_choices
from django.conf import settings


class ParcelForm(forms.ModelForm):
    parcel_number = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': '20450839412914', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Номер посилки',
        max_length=36
    )

    class Meta:
        model = Parcel
        fields = ['parcel_number']


class ReturnRequestForm(forms.Form):
    tracking_number = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': '20450839412914', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Номер посилки',
        max_length=36
    )
    payment_method = forms.ChoiceField(
        label='Споіб платежу',
        choices=[('Cash', 'Готівка'), ('NonCash', 'Карта')],
        widget=forms.Select(attrs={'class': 'form-control mt-2'})
    )
    note = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Note', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Замітки',
        max_length=100,
        required=False
    )
    order_type = forms.CharField(initial='orderCargoReturn', widget=forms.HiddenInput())
    recipient_settlement = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Київ', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Місто отримувача',
        max_length=36
    )
    recipient_settlement_street = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Шевченка', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Вулиця отримувача',
        max_length=36
    )
    building_number = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': '4', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Номер будинку',
        max_length=35
    )
    note_address_recipient = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': '', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Замітки до адреси отримувача',
        max_length=36
    )

    # Custom fields for return reasons and subtypes
    reason_ref = forms.ChoiceField(
        label='Причина повернення',
        choices=get_return_reason_choices(settings.NOVA_POST_API_KEY),
        widget=forms.Select(attrs={'class': 'form-control mt-2'})
    )
    subtype_reason_ref = forms.ChoiceField(
        label='Підпричина повернення',
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control mt-2'})
    )

    def __init__(self, *args, **kwargs):
        super(ReturnRequestForm, self).__init__(*args, **kwargs)

        # Set initial choices for subtype_reason_ref based on the initial value of reason_ref
        initial_reason_ref = self.fields['reason_ref'].initial
        self.fields['subtype_reason_ref'].choices = get_return_subtype_choices(settings.NOVA_POST_API_KEY,
                                                                                   initial_reason_ref)


    def clean_subtype_reason_ref(self):
        # Validate that subtype_reason_ref is selected if reason_ref is selected
        reason_ref = self.cleaned_data.get('reason_ref')
        subtype_reason_ref = self.cleaned_data.get('subtype_reason_ref')

        if reason_ref and not subtype_reason_ref:
            raise forms.ValidationError('Please select a subtype reason.')

        return subtype_reason_ref


class RedirectRequestForm(forms.Form):
    IntDocNumber = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': '20450839412914', 'style': 'width: 300px;', 'class': 'form-control mt-5'}),
        label='Номер посилки',
        max_length=36
    )
    PaymentMethod = forms.ChoiceField(
        label='Спосіб платежу',
        choices=[('Cash', 'Готівка'), ('NonCash', 'Карта')],
        widget=forms.Select(attrs={'class': 'form-control mt-2'})
    )
    Note = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': '', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Замітки',
        max_length=100,
        required=False
    )
    OrderType = forms.CharField(initial='orderRedirecting', widget=forms.HiddenInput())
    RecipientContactName = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Шевченко Андрій Валерійович', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='ПІБ',
        max_length=39
    )
    RecipientPhone = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': '+380959157621', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Номер отримувача',
        max_length=40
    )
    Customer = forms.CharField(initial='Sender', widget=forms.HiddenInput())
    PayerType = forms.ChoiceField(
        label='Payer Type',
        choices=[
            ('Sender', 'Відправник'),
            ('Recipient', 'Отримувач')
        ],
        widget=forms.Select(attrs={'class': 'form-control mt-2'})
    )
    ServiceType = forms.ChoiceField(
        label='Service Type',
        choices=[
            ('DoorsWarehouse', 'Doors to Warehouse'),
            ('WarehouseWarehouse', 'Warehouse to Warehouse')
        ],
        widget=forms.Select(attrs={'class': 'form-control mt-2'})
    )
    RecipientSettlement = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Name', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Recipient Settlement',
        max_length=36
    )
    RecipientSettlementStreet = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Name', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Recipient Settlement Street',
        max_length=36
    )
    BuildingNumber = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Name', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Building Number',
        max_length=36
    )
    NoteAddressRecipient = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Name', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Note Address Recipient',
        max_length=36
    )
    RecipientWarehouseID = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Name', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Recipient Warehouse Id',
        max_length=36
    )
    RecipientWarehouse = forms.CharField(
        widget=forms.HiddenInput(),
        label='Recipient Warehouse',
        max_length=36,
        required=False
    )


class ChangeDataRequestForm(forms.Form):
    IntDocNumber = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Name', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='IntDocNumber',
        max_length=36
    )
    PaymentMethod = forms.ChoiceField(
        label='Payment Method',
        choices=[('Cash', 'Cash'), ('NonCash', 'NonCash')],
        widget=forms.Select(attrs={'class': 'form-control mt-2'})
    )
    OrderType = forms.CharField(initial='orderChangeEW', widget=forms.HiddenInput())
    SenderContactName = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Name', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Sender Contact Name',
        max_length=36
    )
    SenderPhone = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Name', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Sender Phone',
        max_length=37
    )
    RecipientContactName = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Name', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Recipient Contact Name',
        max_length=39,
        required=False
    )
    RecipientPhone = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Name', 'style': 'width: 300px;', 'class': 'form-control mt-2'}),
        label='Recipient Phone',
        max_length=40,
        required=False
    )
    PayerType = forms.ChoiceField(
        label='Payer Type',
        choices=[('Recipient', 'Отримувач'), ('Sender', 'Відправник')],
        widget=forms.Select(attrs={'class': 'form-control mt-2'})
    )


class CustomUserCreationForm(UserCreationForm):
    error_messages = {
        'password_mismatch': "Паролі не співпадають.",
        'password_too_short': "Ваш пароль має містити не менше 8 символів.",
        'password_common': "Ваш пароль не може бути типовим паролем.",
        'password_entirely_numeric': "Ваш пароль не може бути повністю цифровим.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize other labels or help_text if needed

        for field in ['password1', 'password2', 'username']:
            self.fields[field].help_text = None

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if len(password1) < 8:
            raise forms.ValidationError(
                self.error_messages['password_too_short'],
                code='password_too_short',
            )
        # Add more password validation checks as needed
        return password1