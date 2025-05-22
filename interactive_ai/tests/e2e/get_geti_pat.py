# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
"""
This script authenticates against a Geti server and gets a personal access token. Used for BDD e2e tests
"""

import argparse
import datetime
from functools import cached_property
from urllib.parse import parse_qs, urlparse

import requests


class GetiAuthClient:
    def __init__(self, host: str, tls_verify: bool = True):
        self._host = host
        self._session = requests.Session()
        self._session.verify = tls_verify

        # If verify is switched off, disable warnings
        if not tls_verify:
            import urllib3

            urllib3.disable_warnings()

    def login_dex(self, username: str, password: str):
        """
        Login with username/password. Note that it is expected that the server uses Dex as IDP.
        """

        # Query Dex to obtain the login URL
        auth_url = f"{self._host}/dex/auth/regular_users"
        response = self._session.get(
            auth_url,
            params={
                "client_id": "web_ui",
                "redirect_uri": "/callback",
                "scope": "openid profile groups email offline_access",
                "response_type": "code",
                "response_mode": "query",
            },
        )

        if response.status_code != 200:
            raise RuntimeError(f"Unexpected response code {response.status_code} to GET request {auth_url}")

        login_url = response.url

        # Post the login credentials to Dex
        response = self._session.post(
            login_url,
            data={"login": username, "password": password},
            allow_redirects=False,
        )

        if response.status_code != 303:
            raise RuntimeError(f"Unexpected response code {response.status_code} to POST request {login_url}")

        parsed_url = urlparse(response.headers["location"])
        query = parse_qs(parsed_url.query)
        code = query["code"][0]

        # Retrieve the Dex token
        token_url = f"{self._host}/dex/token"
        response = self._session.post(
            token_url,
            data={
                "grant_type": "authorization_code",
                "redirect_uri": "/callback",
                "code": code,
                "client_id": "web_ui",
            },
        )

        if response.status_code != 200:
            raise RuntimeError(f"Unexpected response code {response.status_code} to POST request {token_url}")

        content = response.json()

        # Set the cookies
        id_token = content["id_token"]

        self._session.headers["x-geti-csrf-protection"] = "1"

        url = f"{self._host}/api/v1/set_cookie"
        response = self._session.post(
            url,
            headers={
                "Authorization": f"Bearer {id_token}",
                "x-geti-csrf-protection": "1",
            },
        )

        if response.status_code != 200:
            raise RuntimeError(f"Unexpected response code {response.status_code} to POST request {url}")

    @cached_property
    def organization(self) -> str:
        """
        Return the default organization ID for the active user.
        """

        url = f"{self._host}/api/v1/profile"
        response = self._session.get(url)

        if response.status_code != 200:
            raise RuntimeError(f"Unexpected response code {response.status_code} to POST request {url}")

        content = response.json()

        return content["organizations"][0]["organizationId"]

    @cached_property
    def active_user(self) -> str:
        """
        Return the user ID for the active user.
        """
        url = f"{self._host}/api/v1/organizations/{self.organization}/activeUser"
        response = self._session.get(url)

        if response.status_code != 200:
            raise RuntimeError(f"Unexpected response code {response.status_code} to POST request {url}")

        content = response.json()
        return content["id"]

    def create_pat(self, name, description, expires_at) -> str:
        """
        Create a new personal access token for the active user and return the token ID.
        """
        url = f"{self._host}/api/v1/organizations/{self.organization}/users/{self.active_user}/personal_access_tokens"
        response = self._session.post(
            url,
            json={"name": name, "description": description, "expiresAt": expires_at},
        )

        if response.status_code != 200:
            raise RuntimeError(f"Unexpected response code {response.status_code} to POST request {url}")

        content = response.json()
        return content["personalAccessToken"]

    def list_pat(self) -> dict:
        """
        Return a list of all the personal access token of the active user.
        """
        url = f"{self._host}/api/v1/organizations/{self.organization}/users/{self.active_user}/personal_access_tokens"
        response = self._session.get(url)

        if response.status_code != 200:
            raise RuntimeError(f"Unexpected response code {response.status_code} to POST request {url}")

        content = response.json()
        return content["personalAccessTokens"]

    def delete_pat(self, pat_id: str) -> None:
        """
        Delete a personal access token by ID.
        """
        url = (
            f"{self._host}/api/v1/organizations/{self.organization}/users/{self.active_user}/personal_access_tokens/"
            f"{pat_id}"
        )
        response = self._session.delete(url)

        if response.status_code != 200:
            raise RuntimeError(f"Unexpected response code {response.status_code} to DELETE request {url}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="Geti host to connect to")
    parser.add_argument("--insecure", help="Disable TLS certificate verification", action="store_true")
    parser.add_argument("--username", help="Geti username")
    parser.add_argument("--password", help="Geti password")
    parser.add_argument(
        "--pat-name",
        help="Name of the personal access token",
        default="Geti test client",
    )
    parser.add_argument(
        "--pat-description",
        help="Description of the personal access token",
        default="Geti test client",
    )
    parser.add_argument(
        "--pat-duration",
        help="Duration of the personal access token in hours",
        default=24,
    )
    args = parser.parse_args()

    host = args.host
    if "://" not in host:
        host = "https://" + host

    client = GetiAuthClient(host=host, tls_verify=not args.insecure)
    client.login_dex(args.username, args.password)

    # Delete any previous personal access tokens using the same name.
    for pat in client.list_pat():
        if pat["name"] == args.pat_name:
            client.delete_pat(pat["id"])

    # Create a new personal access token
    date = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=args.pat_duration)).isoformat(
        timespec="seconds",
    )
    print(client.create_pat(args.pat_name, args.pat_description, date))


if __name__ == "__main__":
    main()
