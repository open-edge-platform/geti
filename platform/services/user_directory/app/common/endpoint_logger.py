"""
This file contains a class that extends information logs for endpoints located: /src/gateway/endpoints
"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import asyncio
import inspect
import logging
import os
from functools import wraps

from pydantic.main import BaseModel
from starlette.responses import Response


class EndpointLogger:
    """
    The class contains extend logging of package logger located at: /src/common/common_logger/
    """

    logger = logging.getLogger(__name__)

    @classmethod
    def __is_response_object(cls, suspected_object) -> bool:  # noqa: ANN001
        if isinstance(suspected_object, Response):
            return True
        return issubclass(suspected_object.__class__, Response)

    @classmethod
    def __select_logging_method(cls, my_object):  # noqa: ANN001
        if cls.__is_response_object(suspected_object=my_object):
            object_class = Response
        elif issubclass(my_object.__class__, BaseModel):
            object_class = BaseModel
        else:
            object_class = my_object.__class__

        object_type = {
            Response: cls.__get_response_object_body,
            BaseModel: cls.__show_base_model_logs,
        }

        return object_type.get(object_class, cls.__show_basic_logs)

    @classmethod
    def __show_base_model_logs(cls, base_model_object: BaseModel):
        object_dict = base_model_object.dict()
        do_not_show_key = "password"
        for key, value in object_dict.items():
            if do_not_show_key in key:
                cls.logger.debug(f"{key}:\tXXXXX")
                continue
            cls.logger.debug(f"{key}:\t{value}")

    @classmethod
    def __show_basic_logs(cls, body):  # noqa: ANN001
        if isinstance(body, list) and len(body):
            body = body[0]
        cls.logger.debug(f"{body}")

    @classmethod
    def __get_response_object_body(cls, received_response):  # noqa: ANN001
        try:
            searched_attributes = ["content-type", "body"]
            headers = received_response.headers
            text_type = "text/plain"
            content_type = headers.get(searched_attributes[0], "None")
            cls.logger.debug(f"Status code: {received_response.status_code}")
            cls.logger.debug(f"Content type: {content_type}")
            if text_type in content_type:
                body = received_response.body.decode() if received_response.body else "Empty"
                cls.logger.debug(f"Body: {body}")
        except (UnicodeDecodeError, Exception) as error:
            cls.logger.error(error, stack_info=True, exc_info=True)
            raise

    @classmethod
    def __show_request(cls, request_body: dict):
        cls.logger.debug("Request parameters:")
        for key, _ in request_body.items():
            logs_method = cls.__select_logging_method(request_body[key])
            logs_method(request_body[key])

    @classmethod
    def __show_response(cls, response):  # noqa: ANN001
        cls.logger.debug("Response parameters:")
        selected_method = cls.__select_logging_method(my_object=response)
        selected_method(response)

    @classmethod
    def extended_logging(cls, handler):  # noqa: ANN001
        """
        This method is a decorator which extends the endpoint logs
        """

        if asyncio.iscoroutinefunction(handler):

            @wraps(handler)
            async def wrapper(*args, **kwargs):
                cls.logger.info(f"The Path to the called method: {os.path.abspath(inspect.getfile(handler))}")
                try:
                    cls.__show_request(request_body=kwargs)
                    response = await handler(*args, **kwargs)
                    cls.__show_response(response=response)
                    return response
                except Exception as error:
                    cls.logger.error("Something goes wrong!!")
                    cls.logger.error(error, stack_info=True, exc_info=True)
                    raise

        else:

            @wraps(handler)
            def wrapper(*args, **kwargs):
                cls.logger.info(f"The Path to the called method: {os.path.abspath(inspect.getfile(handler))}")
                try:
                    cls.__show_request(request_body=kwargs)
                    response = handler(*args, **kwargs)
                    cls.__show_response(response=response)
                    return response
                except Exception as error:
                    cls.logger.error("Something goes wrong!!")
                    cls.logger.error(error, stack_info=True, exc_info=True)
                    raise

        return wrapper
