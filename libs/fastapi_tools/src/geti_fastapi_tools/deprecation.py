import json
from datetime import datetime

from fastapi import Response as FastAPIResponse


class RestApiDeprecation:
    """
    A class to handle the addition of deprecation headers to HTTP responses.

    This class provides methods to format deprecation and sunset dates, and to add
    appropriate headers to FastAPI responses indicating the deprecation status of an API.

    :param deprecation_date: The date when the endpoint will be deprecated.
    :param sunset_date: The date or version when the endpoint will be removed.
    :param additional_info: Optional additional information or URL for more details.
    """

    def __init__(
        self,
        deprecation_date: str,
        sunset_date: str,
        additional_info: str | None = None,
    ):
        self.deprecation_date = deprecation_date
        self.sunset_date = sunset_date
        self.additional_info = additional_info

    def add_headers(self, content: dict) -> FastAPIResponse:
        """
        Adds deprecation headers to the HTTP response.

        :param content: The HTTP response object (FastAPIResponse).
        :return: The modified response with deprecation headers.
        """
        headers = {
            "Deprecation": self._format_deprecation_date(),
            "Sunset": self._format_sunset_date_or_version(),
        }

        if self.additional_info:
            headers["Link"] = f'<{self.additional_info}>; rel="deprecation-info"'

        return FastAPIResponse(content=json.dumps(content), headers=headers)

    def _format_deprecation_date(self) -> str:
        """Formats the deprecation date as a Unix timestamp."""
        try:
            return str(self._convert_date_time_to_unix_timestamp(f"{self.deprecation_date} 00:00:00"))
        except ValueError:
            raise ValueError("deprecation_date must be in 'YYYY-MM-DD' format.")

    def _format_sunset_date_or_version(self) -> str:
        """Formats the sunset date as an HTTP-date or returns the version if applicable."""
        try:
            if self.sunset_date.startswith("v"):
                return self.sunset_date
            sunset_datetime = datetime.strptime(self.sunset_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            return sunset_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT")
        except ValueError:
            raise ValueError("sunset_date must be in 'YYYY-MM-DD' format or a version string starting with 'v'.")

    @staticmethod
    def _convert_date_time_to_unix_timestamp(date_time: str) -> int:
        """
        Converts a date-time string to a Unix timestamp.
        Example: "2024-11-24 23:00:00" (GMT+0000) becomes 1732489200.

        :param date_time: The date-time string in the format "YYYY-MM-DD HH:MM:SS".
        :return: The Unix timestamp as an integer.
        """
        return int(datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S").timestamp())
