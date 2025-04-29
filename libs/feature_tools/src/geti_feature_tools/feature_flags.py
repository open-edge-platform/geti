# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os
from enum import Enum

logger = logging.getLogger(__name__)


class FeatureFlagProvider:
    @staticmethod
    def _str2bool(text: str) -> bool:
        """
        Converts a string to a boolean based on common true/false representations.
        Recognizes the following as True: {"y", "yes", "t", "true", "on", "1"}
        Recognizes the following as False: {"n", "no", "f", "false", "off", "0"}
        Raises ValueError for any other inputs.
        This is similar to the behavior of distutils.util.strtobool.

        :param text: string to convert to boolean
        :return: boolean of the input string
        :raises ValueError: if the logical value cannot be determined

        """

        TRUE_SET = {"y", "yes", "t", "true", "on", "1"}
        FALSE_SET = {"n", "no", "f", "false", "off", "0"}
        buf_input = text.lower()
        if buf_input in TRUE_SET:
            return True
        if buf_input in FALSE_SET:
            return False
        raise ValueError(f"Cannot convert {text} to boolean. Expected one of {TRUE_SET} or {FALSE_SET}")

    @classmethod
    def is_enabled(cls, feature_flag: str | Enum) -> bool:
        """
        Returns whether the provided feature flag is enabled

        :param feature_flag: name of the feature flag to check
        :return: True if enabled, false otherwise
        """
        feature_flag_str = feature_flag.name if isinstance(feature_flag, Enum) else feature_flag
        feature_flag_value = os.environ.get(feature_flag_str)
        if feature_flag_value is None:
            logger.warning(f"Attempting to access undefined flag '{feature_flag_str}'; assuming value False.")
            return False
        return cls._str2bool(feature_flag_value)
