import logging

from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpRequest
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_email_util(
    subject_template_name,
    email_template_name,
    context,
    from_email,
    to_email,
    request=None,
):

    # Request object is required to get site name
    if request is None:
        raise ValueError("Request must be provided to send_email_util")

    if not isinstance(request, HttpRequest):
        raise TypeError("Request must be an instance of HttpRequest")

    current_site = get_current_site(request)
    context.update(
        {
            "site_name": current_site.domain,
        }
    )

    """Send a django.core.mail.EmailMessage to `to_email`."""
    subject = render_to_string(subject_template_name, context)
    subject = "".join(subject.splitlines())
    body = render_to_string(email_template_name, context)
    email_message = EmailMessage(subject, body, from_email, [to_email])

    try:
        email_message.send()
    except Exception:
        logger.exception(
            f"Failed to send email '{render_to_string(subject_template_name)}' "
            f"to {to_email}"
        )
