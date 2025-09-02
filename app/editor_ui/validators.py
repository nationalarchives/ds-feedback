from django.core.validators import RegexValidator
from django.forms import ValidationError


def validate_path_pattern(value):
    """
    Validates a URL path pattern:
    - Must start and end with forward slash
    - Must contain only valid URL characters
    - Must not contain potential injection patterns
    """
    # ensure pattern starts and ends with slash
    if not value.startswith("/"):
        raise ValidationError("Pattern must start with a forward slash (/)")
    if not value.endswith("/"):
        raise ValidationError("Pattern must end with a forward slash (/)")

    path_parts = [part for part in value.split("/") if part]

    sanitized_parts = []
    for part in path_parts:
        print(f"Processing part: {part}")

        # Remove directory segments
        if part in [".", ".."]:
            continue

        if part:
            # Only add non-empty parts
            sanitized_parts.append(part)

    sanitized = "/" + "/".join(sanitized_parts) + "/"

    # normalize multiple slashes
    while "//" in sanitized:
        sanitized = sanitized.replace("//", "/")

    # Use Django's RegexValidator for the valid characters check
    path_validator = RegexValidator(
        regex=r"^[a-zA-Z0-9\-_\./%]+$",
        message="Pattern contains invalid characters. Only letters, numbers, hyphens, "
        "underscores, periods, forward slashes, and percent encodings are allowed.",
    )

    path_validator(sanitized)

    return sanitized
