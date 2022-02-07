import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from app.core.config import settings


jinja_emails_env = Environment(loader=FileSystemLoader(Path(settings.EMAIL_TEMPLATES_DIR)))


def send_email(email_to: str, subject_template: str = "", html_template: str = "", text_template: str = "") -> None:
    assert settings.EMAILS_ENABLED, "no provided configuration for email variables"
    message = MIMEMultipart("alternative")
    message['Subject'] = subject_template
    message['From'] = settings.EMAILS_FROM_EMAIL
    message['To'] = email_to

    text_body = MIMEText(text_template, "plain")
    html_body = MIMEText(html_template, "html")
    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(text_body)
    message.attach(html_body)

    # Create a secure SSL context
    context = ssl.create_default_context()
    # Using .starttls() with a Gmail Account set for Development
    try:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.START_TLS_PORT)
        server.starttls(context=context)  # Secure the connection
        server.login(settings.EMAILS_FROM_EMAIL, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAILS_FROM_EMAIL, email_to, message.as_string())
    except Exception as e:
        raise e
    finally:
        server.quit()

    # Setting up a Local SMTP Server
    # $ sudo python -m smtpd -c DebuggingServer -n localhost:1025
    # try:
    #     local_server = smtplib.SMTP("localhost", settings.SMTP_LOCAL_PORT)
    #     local_server.sendmail(settings.EMAILS_FROM_EMAIL, "fake@mail.com", message.as_string())
    # except Exception as e:
    #     # Print any error messages to stdout
    #     raise e
    # finally:
    #     local_server.quit()


def send_new_account_email(email_to: str) -> None:
    data = {
        "project_name": settings.PROJECT_NAME,
        "subject": f"{settings.PROJECT_NAME} - New account for user with email {email_to}",
        "email_to": email_to,
        "link": settings.API_DOCS_LINK
    }
    html_template = jinja_emails_env.get_template('new_account.html').render(**data)
    text_template = jinja_emails_env.get_template('new_account.txt').render(**data)
    send_email(email_to, data["subject"], html_template, text_template)


def send_reset_api_key_email(email_to: str, token: str) -> None:
    data = {
        "project_name": settings.PROJECT_NAME,
        "subject": f"{settings.PROJECT_NAME} - API Key recovery for user with email {email_to}",
        "email_to": email_to,
        "expire_link_hr": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
        "link": Path(settings.API_LINK) / f"login/reset-api-key-form?email={email_to}&token={token}"
    }
    html_template = jinja_emails_env.get_template('reset_api_key_email.html').render(**data)
    text_template = jinja_emails_env.get_template('reset_api_key_email.txt').render(**data)
    send_email(email_to, data["subject"], html_template, text_template)
