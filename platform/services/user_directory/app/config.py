# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Configuration file
"""

import os

IMPT_CONFIGURATION_CM = os.getenv("IMPT_CONFIGURATION_CM", "impt-configuration")
K8S_CR_NAMESPACE = os.getenv("K8S_CR_NAMESPACE", "default")
USE_KUBECONFIG = os.getenv("USE_KUBECONFIG", "False").lower() == "true"

# Auth settings
LDAP_HOST = os.getenv("LDAP_HOST", "impt-openldap")
LDAP_PORT = int(os.getenv("LDAP_PORT", "389"))
LDAP_ADMIN_USER = f"cn={os.getenv('LDAP_ADMIN_USER', 'admin')},dc=example,dc=org"
LDAP_ADMIN_PASSWORD = os.getenv("LDAP_ADMIN_PASSWORD", "admin")
AUTH_CONFIG = {"user": LDAP_ADMIN_USER, "password": LDAP_ADMIN_PASSWORD, "host": LDAP_HOST, "port": LDAP_PORT}
VERIFY_HTTPS = os.getenv("ALLOW_NO_SECURE_HTTP", "false").lower() == "true"

# email templates with smtp configuration related parameters
EMAIL_TEMPLATES_CM = os.getenv("EMAIL_TEMPLATES_CM", "impt-email-templates")
SMTP_CONFIGURATION_SECRET = os.getenv("SMTP_CONFIGURATION_SECRET", "impt-email-config")
JWT_SECRET = os.getenv("JWT_SECRET", "impt-jwt-config")

IMPT_RESOURCE_SERVICE_HOST = os.getenv("IMPT_RESOURCE_SERVICE_HOST", "10.0.0.0")
IMPT_RESOURCE_SERVICE_PORT = int(os.getenv("IMPT_RESOURCE_SERVICE_PORT", "5000"))
