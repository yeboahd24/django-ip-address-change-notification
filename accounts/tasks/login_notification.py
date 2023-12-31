from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags


@shared_task
def send_login_notification_email(email, html_content):
    # Create an EmailMessage
    user_email_func = EmailMultiAlternatives(
        subject="Login from a Different Location",
        body=strip_tags(html_content),  # Use the text version of the HTML content
        from_email="mesika@gmail.com",
        to=[email],
    )

    # Attach the HTML content to the email
    user_email_func.attach_alternative(html_content, "text/html")

    # Send the email
    user_email_func.send()
