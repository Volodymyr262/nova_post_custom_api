# forms.py
from django import forms
from .models import Parcel


class ParcelForm(forms.ModelForm):
    class Meta:
        model = Parcel
        fields = ['parcel_number']


class ReturnRequestForm(forms.Form):
    tracking_number = forms.CharField(label='Tracking Number', max_length=36)
    payment_method = forms.ChoiceField(
        label='Payment Method',
        choices=[('Cash', 'Cash'), ('NonCash', 'NonCash')],
    )
    reason = forms.CharField(label='Reason', max_length=36)
    subtype_reason = forms.CharField(label='Subtype Reason', max_length=36)
    note = forms.CharField(label='Note', max_length=100, required=False)
    order_type = forms.CharField(initial='orderCargoReturn', widget=forms.HiddenInput())
    recipient_settlement = forms.CharField(label='Recipient Settlement', max_length=36)
    recipient_settlement_street = forms.CharField(label='Recipient Settlement Street', max_length=36)
    building_number = forms.CharField(label='Building Number', max_length=35)
    note_address_recipient = forms.CharField(label='Note Address Recipient', max_length=36)