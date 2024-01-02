# forms.py
from django import forms
from .models import Parcel
from .moduls import get_return_reason_choices, get_return_subtype_choices
from django.conf import settings


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
    note = forms.CharField(label='Note', max_length=100, required=False)
    order_type = forms.CharField(initial='orderCargoReturn', widget=forms.HiddenInput())
    recipient_settlement = forms.CharField(label='Recipient Settlement', max_length=36)
    recipient_settlement_street = forms.CharField(label='Recipient Settlement Street', max_length=36)
    building_number = forms.CharField(label='Building Number', max_length=35)
    note_address_recipient = forms.CharField(label='Note Address Recipient', max_length=36)

    # Custom fields for return reasons and subtypes
    reason_ref = forms.ChoiceField(label='Reason', choices=get_return_reason_choices(settings.NOVA_POST_API_KEY))
    subtype_reason_ref = forms.ChoiceField(label='Subtype Reason', choices=[])

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