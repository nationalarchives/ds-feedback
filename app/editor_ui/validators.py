from django.core.validators import RegexValidator
from django.forms import ValidationError


def validate_path_pattern(value):
    """
    Validates a URL path pattern:
    - Must start with a forward slash
    - Must end with a forward slash or asterisk
    - Must contain only valid URL characters
    """
    # check if pattern starts with forward slash
    if not value.startswith("/"):
        raise ValidationError("Pattern must start with a forward slash (/)")

    # check if pattern ends with forward slash or asterisk
    if not value.endswith(("/", "*")):
        raise ValidationError(
            "Pattern must end with a forward slash (/) or asterisk (*)"
        )

    # check asterisk is at the end of the pattern
    if "*" in value and not value.endswith("*"):
        raise ValidationError(
            "Asterisk (*) is only allowed at the end of the pattern"
        )

    # check for multiple asterisks
    if value.count("*") > 1:
        raise ValidationError("Only one asterisk (*) is allowed in the pattern")

    # use RegexValidator to ensure the pattern contains valid characters
    path_validator = RegexValidator(
        regex=r"^[a-zA-Z0-9\-_\./%~\*]+$",
        message="Pattern contains invalid characters. Only letters, numbers, hyphens, "
        "underscores, periods, forward slashes, percent encodings, tildes, and asterisks are allowed.",
    )

    path_validator(value)
