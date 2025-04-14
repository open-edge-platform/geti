# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module define the color entity."""

import random


class Color:
    """Represents an RGBA color."""

    def __init__(self, red: int, green: int, blue: int, alpha: int = 255):
        self.red = red
        self.green = green
        self.blue = blue
        self.alpha = alpha

    def __repr__(self):
        """Returns string representation of the color."""
        return f"Color(red={self.red}, green={self.green}, blue={self.blue}, alpha={self.alpha})"

    def __eq__(self, other: object) -> bool:
        """Returns True if both colors are equal."""
        if isinstance(other, Color):
            return (
                self.red == other.red
                and self.green == other.green
                and self.blue == other.blue
                and self.alpha == other.alpha
            )
        return False

    @property
    def hex_str(self) -> str:
        """Returns the color in a Hex representation."""
        return f"#{self.red:02x}{self.green:02x}{self.blue:02x}{self.alpha:02x}"

    @classmethod
    def from_hex_str(cls, string: str) -> "Color":
        """
        Creates Color() instance given a hex string.

        Supports 6 character hex string (RGB), or 8 character hex string (RGBA).
        The string might optionally start with a number sign (#).

        Example:
            Creating color object:

            >>> Color.from_hex_str("#ff0000")
            Color(red=255, green=0, blue=0, alpha=255)

            >>> Color.from_hex_str("0000ff")
            Color(red=0, green=0, blue=255, alpha=255)

            >>> Color.from_hex_str("#96Ff00C8")
            Color(red=150, green=255, blue=0, alpha=200)

        :param string (str): Hex string
        :returns: Color instance
        """
        string = string.lstrip("#").lower()
        if len(string) < 8:
            # If alpha channel misses, add it
            string += (8 - len(string)) * "f"
        red, green, blue, alpha = tuple(int(string[i : i + 2], 16) for i in (0, 2, 4, 6))
        return cls(red=red, green=green, blue=blue, alpha=alpha)

    @classmethod
    def random(cls) -> "Color":
        """
        Generate random Color() instance.

        :returns: Color instance with random color
        """
        red, green, blue = (
            # disable B311 random - used for the random sampling not for security/crypto
            random.randint(0, 255),  # nosec: B311 # noqa: S311
            random.randint(0, 255),  # nosec B311 # noqa: S311
            random.randint(0, 255),  # nosec B311 # noqa: S311
        )
        return cls(red=red, green=green, blue=blue, alpha=255)

    @property
    def rgb_tuple(self) -> tuple[int, int, int]:
        """Retrieves the Color as a RGB tuple."""
        return self.red, self.green, self.blue

    @property
    def bgr_tuple(self) -> tuple[int, int, int]:
        """Retrieves the Color as a BGR tuple."""
        return self.blue, self.green, self.red
