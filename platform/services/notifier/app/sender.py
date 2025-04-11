# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import re
from email.headerregistry import Address
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from aiosmtplib import SMTPException, send

from message import Message

from config import SMTP_HOST, SMTP_LOGIN, SMTP_PASSWORD, SMTP_PORT, USE_START_TLS, VERIFY_HTTPS

logger = logging.getLogger(__name__)


def is_valid_email(mail: str) -> bool:
    """Validates email address format"""
    regex = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
    if re.fullmatch(regex, mail):
        return True
    raise ValueError(f"Invalid email: {mail}")


def create_email_message(message: Message) -> MIMEMultipart:
    """
    Create email message from Message object
    """
    if not is_valid_email(message.from_address):
        raise ValueError('Invalid "From" email address')
    if not is_valid_email(message.to):
        raise ValueError('Invalid "To" email address')

    msg = MIMEMultipart()
    msg["From"] = str(Address(display_name=message.from_name, addr_spec=message.from_address))
    msg["Subject"] = message.subject
    msg["To"] = message.to

    if message.content:
        msg.attach(MIMEText(message.content, "plain", "utf-8"))

    if message.html_content:
        msg.attach(MIMEText(message.html_content, "html", "utf-8"))

    return msg


async def send_message(message: Message) -> None:
    """
    Send the message in a background task.
    """
    logger.info("Sending email")

    msg = create_email_message(message=message)

    validate_certs = VERIFY_HTTPS

    try:
        await send(
            message=msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_LOGIN,
            password=SMTP_PASSWORD,
            start_tls=USE_START_TLS,
            use_tls=not USE_START_TLS,
            validate_certs=validate_certs,
        )
        logger.info("Email sent successfully")
    except SMTPException as e:
        logger.exception(f"Error during sending email: {e}")
