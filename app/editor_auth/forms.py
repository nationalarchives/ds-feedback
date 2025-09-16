from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)


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


class CustomPasswordResetForm(PasswordResetForm):
    """
    Custom login form with styled fields and additional features
    """

    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "class": "tna-text-input",
                "name": "email",
                "type": "email",
                "spellcheck": "false",
                "autocapitalize": "off",
                "autocorrect": "off",
            }
        ),
    )


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="New password",
        required=True,
        strip=False,
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
        ),
        # help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label="New password confirmation",
        required=True,
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
        ),
        strip=False,
        help_text="Enter the same password as before, for verification.",
    )
