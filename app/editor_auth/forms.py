from django import forms
from django.contrib.auth.forms import AuthenticationForm


class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom login form with styled fields and additional features
    """

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "tna-text-input",
                "name": "username",
                "type": "text",
                "spellcheck": "false",
                "autocapitalize": "off",
                "autocorrect": "off",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "tna-text-input",
                "name": "password",
                "type": "password",
                "autocapitalize": "off",
                "autocomplete": "off",
                "autocorrect": "off",
                "spellcheck": "false",
            }
        )
    )
