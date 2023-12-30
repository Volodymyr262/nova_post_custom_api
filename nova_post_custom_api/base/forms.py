# forms.py
from django import forms
from .models import Parcel


class ParcelForm(forms.ModelForm):
    class Meta:
        model = Parcel
        fields = ['parcel_number']
