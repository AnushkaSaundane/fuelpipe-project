from django import forms
from .models import PartRequest


class PartRequestForm(forms.ModelForm):
    class Meta:
        model = PartRequest
        fields = "__all__"