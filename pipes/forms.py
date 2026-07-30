from django import forms
from .models import ProductRequest


class ProductRequest(forms.ModelForm):
    class Meta:
        model = ProductRequest
        fields = "__all__"