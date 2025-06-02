from django import forms
from .models import Vpn, Interface


class CreateVpn(forms.ModelForm):
    class Meta():
        model = Vpn
        fields = '__all__'

class CreateInterface(forms.ModelForm):
    class Meta():
        model = Interface
        fields = '__all__'