from pathlib import Path
from smtplib import SMTPRecipientsRefused, SMTPAuthenticationError

import pytest
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from app.core.config import settings
from app.utils.email_utils import send_email, send_new_account_email, jinja_env


def test_send_email_wrong_recipient_address() -> None:
    with pytest.raises(Exception) as e:
        send_email("wrong email address", "My test mail subject", "html_template", "text_template")
    assert e.type == SMTPRecipientsRefused


def test_send_email_wrong_host_login_user(mocker) -> None:
    mocker.patch.object(settings, 'EMAILS_FROM_EMAIL', "wrong login user")
    with pytest.raises(Exception) as e:
        send_email("", "My test mail subject", "html_template", "text_template")
    assert e.type == SMTPAuthenticationError


def test_send_email_wrong_login_password(mocker) -> None:
    mocker.patch.object(settings, 'SMTP_PASSWORD', "wrong password")
    with pytest.raises(Exception) as e:
        send_email("", "My test mail subject", "html_template", "text_template")
    assert e.type == SMTPAuthenticationError


def test_send_new_account_email(mocker) -> None:
    jinja_env = Environment()
    email_to = ""
    data = {
        "project_name": settings.PROJECT_NAME,
        "subject": f"{settings.PROJECT_NAME} - New account for user with email {email_to}",
        "email_to": email_to,
        "link": settings.API_DOCS_LINK
    }
    # reproduce templates directly from file (instead of using Jinja Env. loader as in tested function)
    with open(Path(settings.EMAIL_TEMPLATES_DIR) / 'new_account.html') as html_file:
        html_str = html_file.read()
        html_template = jinja_env.from_string(html_str).render(**data)
    with open(Path(settings.EMAIL_TEMPLATES_DIR) / 'new_account.txt') as text_file:
        text_str = text_file.read()
        text_template = jinja_env.from_string(text_str).render(**data)

    mock_send_email = mocker.patch('app.utils.email_utils.send_email')
    send_new_account_email(email_to)
    mock_send_email.assert_called_with("", data["subject"], html_template, text_template)


def test_send_new_account_email_not_existing_template_raises_exception(mocker) -> None:
    mocker.patch.object(jinja_env, 'loader', FileSystemLoader(Path("wrong path")))
    with pytest.raises(Exception) as e:
        send_new_account_email("")
    assert e.type == TemplateNotFound
