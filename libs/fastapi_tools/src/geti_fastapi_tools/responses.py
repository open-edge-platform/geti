from fastapi.encoders import jsonable_encoder


def success_response_rest() -> dict:
    """
    Shortcut for returning a success response dictionary
    """
    return {"result": "success"}


def error_response_rest(error_code: str, message: str = "", http_status: int = 500) -> dict[str, str | int]:
    """
    Returns a json with error information

    :param error_code:  name for error (snake cased)
    :param message: Additional message to describe error
    :param http_status: HTTP Response Status code
    """
    return jsonable_encoder({"error_code": error_code, "message": message, "http_status": http_status})
