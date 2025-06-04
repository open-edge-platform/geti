# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

"""
Strings that are shown to the user by validators functions.
"""


class EmailValidatorsTexts:
    """
    Strings that are shown to the user during email validation.
    """

    invalid_email = "{mail} is not a valid email address."


class PasswordValidatorsTexts:
    """
    Strings that are shown to the user during password validation.
    """

    invalid_password = (
        "Password must consist of 8 - 200 characters at least one capital letter, lower letter, digit or symbol."  # noqa: S105
    )


class PathValidatorsTexts:
    """
    Strings that are shown to the user during path validation.
    """

    invalid_path = "Provided path {path} format is not correct. It must be an absolute path (e.g. {folder})."
    path_not_exists = (
        "Provided path {path} does not point to an existing folder. It must be an absolute path (e.g. {folder})."
    )
    path_not_folder = "Provided path {path} does not point to a folder."
    path_already_exists = "Cannot create {path}. Please delete the folder or use '--data-folder' parameter and point to existing directory."
    path_not_empty = "Provided folder {path} is not empty."
    invalid_permissions = "Provided folder {path} has too open permissions {permissions}. Recommended are 750."
    path_permission_error = "Provided path {path} has wrong access permission. Please check your permissions."


class DomainValidatorsTexts:
    """
    Strings that are shown to the user during domain validation.
    """

    empty_domain = "domain is empty."
    invalid_name = "Provided name {name} does not have a valid format."


class FilepathValidatorsTexts:
    """
    Strings that are shown to the user during filepath validation.
    """

    invalid_filepath = (
        "Provided file {filepath} is not valid. Filepath must be an absolute path (e.g. /home/user/filename)"
    )
    filepath_not_exists = "Provided file {filepath} does not exists on the filesystem."
    filepath_not_readable = "Provided file {filepath} is not readable or has wrong access permission."


class MailServerValidatorsTexts:
    """
    Strings that are shown to the user during SMTP server validation.
    """

    connection_failed = "Unable to connect to Mail Server ({host}:{port})"
