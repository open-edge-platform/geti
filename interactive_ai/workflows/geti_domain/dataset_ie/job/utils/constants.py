# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os

logger = logging.getLogger(__name__)
if not logger.hasHandlers() and logger.getEffectiveLevel() == logging.WARNING:
    # Setup the logger if this is imported before the common logger initialization code
    logging.basicConfig()
    logger.setLevel(logging.INFO)

##############################################################################
# Restrictions on media uploads
# TODO Need to share constants @ microservices/utils/constants.py


def _get_env_var(var_name: str, default_value: int | None = None):
    value: str = os.environ.get(var_name, "")
    if value == "":
        message = f"{var_name} was not configured explicitly, "
        if not default_value:
            message += "it won't be enforced."
        else:
            message += f"it will be enforced as `{default_value}`."
        logger.info(message)
        return default_value
    try:
        logger.info(f"{var_name} is configured as `{int(value)}`.")
        return int(value)
    except (ValueError, TypeError):
        try:
            logger.info(f"{var_name} is configured as `{int(float(value))}`.")
            return int(float(value))
        except (ValueError, TypeError):
            message = f"{var_name} was configured explicitly as `{value}`, "
            message += "but couldn't convert it into a numeric value. "
            if not default_value:
                message += "It won't be enforced."
            else:
                message += f"It will be enforced as `{default_value}`."
            logger.warning(message)
            return default_value


# The maximum number of dataset storages allowed
MAX_NUMBER_OF_DATASET_STORAGES: int | None = _get_env_var("MAX_NUMBER_OF_DATASET_STORAGES")

# The maximum number of media (images + videos) in a project
MAX_NUMBER_OF_MEDIA_PER_PROJECT: int | None = _get_env_var("MAX_NUMBER_OF_MEDIA_PER_PROJECT")

# Maximum number of pixels allowed in an image.
# Note that this limit does NOT refer to the individual dimensions (width, height) of the media, but to their product.
# In other words, this limit triggers if: (width x height) > MAX_NUMBER_OF_PIXELS
MAX_NUMBER_OF_PIXELS: int | None = _get_env_var("MAX_NUMBER_OF_PIXELS")


MIN_IMAGE_SIZE = _get_env_var("MIN_IMAGE_SIZE", 32)  # pixels
MAX_IMAGE_SIZE = _get_env_var("MAX_IMAGE_SIZE", 20000)  # pixels
MIN_VIDEO_SIZE = _get_env_var("MIN_VIDEO_SIZE", 32)  # pixels
MAX_VIDEO_WIDTH = _get_env_var("MAX_VIDEO_WIDTH", 7680)  # pixels
MAX_VIDEO_HEIGHT = _get_env_var("MAX_VIDEO_HEIGHT", 4320)  # pixels
MAX_VIDEO_LENGTH = _get_env_var("MAX_VIDEO_LENGTH", 10800)  # seconds (=3hours)
