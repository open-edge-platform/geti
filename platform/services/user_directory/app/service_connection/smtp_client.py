# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
# isort:skip_file

"""This module contains the implementation of the SMTP Client."""

import logging
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from smtplib import (
    SMTP,
    SMTP_SSL,
    SMTPDataError,
    SMTPHeloError,
    SMTPNotSupportedError,
    SMTPRecipientsRefused,
    SMTPSenderRefused,
)

from jinja2 import Template
from service_connection.k8s_client.secrets import get_secrets
from service_connection.k8s_client.config_maps import get_config_map

from config import VERIFY_HTTPS, SMTP_CONFIGURATION_SECRET, EMAIL_TEMPLATES_CM

logger = logging.getLogger(__name__)


class EmailTemplates(Enum):
    """
    This Enum represents the available email templates.
    """

    INVITATION_MAIL = "InvitationMail"
    PASSWORD_RESET = "PasswordReset"  # noqa: S105


class SMTPClient:
    """
    Simple implementation of smtp client.
    """

    def __init__(self, debug=None) -> None:  # noqa: ANN001
        self._get_mail_server_configuration_from_secret()
        if self.smtp_port == 465:
            self.client = SMTP_SSL(host=self.smtp_host, port=self.smtp_port, context=ssl.create_default_context())
            logger.debug("Login into SMTP using credentials.")
            self.client.login(self.smtp_login, self.smtp_password)
        else:
            self.client = SMTP(host=self.smtp_host, port=self.smtp_port)  # type: ignore
            self._connect_with_tls()
        if debug:
            self.client.set_debuglevel(2)

    def _get_mail_server_configuration_from_secret(self):
        """
        Loads SMTP server configuration stored in k8s secret.
        """
        logger.debug(f"Extract SMTP server configuration from k8s `{SMTP_CONFIGURATION_SECRET}` secret.")
        smtp = get_secrets(
            name=SMTP_CONFIGURATION_SECRET,
            secrets_list=["from_mail", "from_name", "smtp_port", "smtp_login", "smtp_password", "smtp_host"],
        )

        self.from_mail = smtp["from_mail"]
        self.from_name = smtp["from_name"]
        self.smtp_port = smtp["smtp_port"]
        self.smtp_login = smtp["smtp_login"]
        self.smtp_password = smtp["smtp_password"]
        self.smtp_host = smtp["smtp_host"]

    @staticmethod
    def _get_email_template_from_cm(template: str) -> dict[str, str]:
        """
        Loads email template from k8s config map based on name of template
        :param template: name of email template
        :return: dictionary with topic and message of email template
        :raise: KeyError when `topic` and/or `message` does not exist in configmap
        """
        email_templates = get_config_map(name=EMAIL_TEMPLATES_CM)

        topic = email_templates[f"{template}Topic"]
        message = email_templates[f"{template}Message"]
        return {"topic": topic, "message": message}

    def _connect(self):
        """
        Login for testing purposes.
        """
        self.client.login(self.smtp_login, self.smtp_password)

    def _connect_with_tls(self):
        """
        Login into SMTP server with starttls enabled.
        """
        if VERIFY_HTTPS:
            default_ciphers = (
                "ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+HIGH:"
                "DH+HIGH:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+HIGH:RSA+3DES:!aNULL:"
                "!eNULL:!MD5"
            )
            # only TLSv1 or higher
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            context.options |= ssl.OP_NO_SSLv2
            context.options |= ssl.OP_NO_SSLv3
            context.set_ciphers(default_ciphers)
            context.set_default_verify_paths()
            context.verify_mode = ssl.CERT_REQUIRED
        else:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        logger.debug("Invoke starttls.")
        if self.client.starttls(context=context)[0] != 220:
            raise Exception("Exiting because connection if not encrypted.")  # cancel if connection is not encrypted
        logger.debug("Login into SMTP using credentials.")
        self.client.login(self.smtp_login, self.smtp_password)

    @staticmethod
    def _render_template(template: str, template_vars: dict[str, str]) -> tuple[str, str]:
        """
        Renders provided template using provided template variables.
        :param template: template to render
        :param template_vars: variables to fill template
        :return: rendered topic and message of email
        """
        email_template = SMTPClient._get_email_template_from_cm(template=template)
        message = Template(email_template["message"])
        topic = Template(email_template["topic"])
        return topic.render(template_vars), message.render(template_vars)

    def ping(self):  # noqa: ANN201
        """
        Function used for connection testing.
        :return: 'OK' when connected,'NOK' otherwise
        """
        if self.client.noop()[0] == 250:
            return self.client.noop()[1].decode("UTF-8")
        return "NOK"

    def send_email(self, template: EmailTemplates, template_vars: dict[str, str], to_field: str):  # noqa: ANN201
        """
        Main method in SMTP client
        :param template: name of email template to use
        :param template_vars: values for substitution in template
        :param to_field: where to send email
        """
        subject, body = self._render_template(template=template.value, template_vars=template_vars)
        msg = MIMEMultipart("alternative")
        msg["From"] = self.from_mail
        msg["Subject"] = subject
        msg["To"] = to_field

        msg.attach(MIMEText(body, "html"))
        try:
            logger.info("Sending email.")
            self.client.sendmail(self.from_mail, to_field, msg.as_string())
        except (SMTPHeloError, SMTPRecipientsRefused, SMTPSenderRefused, SMTPDataError, SMTPNotSupportedError) as exp:
            logger.error("Error sending email.")
            logger.exception(str(exp))
            raise

    def close(self):  # noqa: ANN201
        """
        Closes connection to SMTP server.
        """
        logger.debug("Close connection to SMTP server.")
        self.client.quit()


def run():  # noqa: ANN201
    """
    Example of usage of SMTPClient.
    1. Instantiate SMTPClient
    2. invoke ping, to verify connectivity
    3. send email based on template available in CM
    4. close connection
    """
    client = SMTPClient(debug=True)
    # _ = client.ping()
    client.send_email(
        template=EmailTemplates.INVITATION_MAIL,
        template_vars={"invitationLink": "link_testowy", "ala": "ma"},
        to_field="qwerty",
    )
    client.close()


if __name__ == "__main__":
    run()
