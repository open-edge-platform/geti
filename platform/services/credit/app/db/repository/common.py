# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import inspect
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from sqlalchemy import Result, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def transactional(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    This decorator manages a database transaction, committing the transaction after the function's
    execution or rolling it back in case of an error.
    It checks if the function call is already within a transaction to avoid multiple commits.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        db_session = bound_args.arguments.get("_db_session")
        if db_session is None:
            raise RuntimeError("'_db_session' argument is required but not provided.")

        if getattr(db_session, "_in_transaction", False):
            # If already in a transaction, directly call the function
            return func(*args, **kwargs)

        try:
            setattr(db_session, "_in_transaction", True)  # Indicate that a transaction is in progress
            result = func(*args, **kwargs)
            db_session.commit()
            return result
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error during transaction, rolling back. Error: {e}")
            logger.error(e, exc_info=True)
            raise e
        finally:
            setattr(db_session, "_in_transaction", False)  # Reset the transaction indicator

    return wrapper


def advisory_lock(lock_string_name: str) -> Callable[..., Any]:
    """
    This decorator factory is supposed to be chained with the 'transactional' decorator.
    It obtains exclusive session-level advisory lock, based on the specified
    lock string parameter (usually 'organization_id').
    The lock is released explicitly, once the wrapped function finishes its execution.

    Multiple session-level lock requests stack, so that it's possible to successfully lock
    the same resource identifier several times within a session.

    Returns:
        Callable[..., Any]: A decorator that wraps the given function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            lock_string = bound_args.arguments.get(lock_string_name)
            db_session = bound_args.arguments.get("_db_session")
            if lock_string is None:
                raise RuntimeError(
                    f"The specified lock string '{lock_string_name}' is not found in the arguments of the decorated "
                    f"function."
                )
            if db_session is None:
                raise RuntimeError(
                    "'_db_session' argument is required, but not provided in the arguments of the decorated function."
                )

            lock_key = generate_lock_key(lock_string)
            acquire_advisory_lock(db_session, lock_key)
            logger.debug(f"Acquired advisory lock with key {lock_string}.")

            try:
                wrapped_result = func(*args, **kwargs)
            finally:
                is_lock_released = release_advisory_lock(db_session, lock_key)
                if not is_lock_released:
                    raise RuntimeError(f"Advisory lock with key {lock_key} was not held.")
                logger.debug(f"Released advisory lock with key {lock_string}.")

            return wrapped_result

        return wrapper

    return decorator


def generate_lock_key(lock_string: str) -> int:
    """
    Creates lock key for given string using Python's default hash function.
    """
    bigint_max_value = 9223372036854775807
    return hash(lock_string) % (bigint_max_value + 1)


def acquire_advisory_lock(session: Session, lock_key: int) -> None:
    """
    Obtains an exclusive session-level advisory lock, waiting if necessary.
    The lock is released either explicitly or automatically at the end of a session.
    """
    session.execute(text("SELECT pg_advisory_lock(:lock_key)"), {"lock_key": lock_key})


def release_advisory_lock(session: Session, lock_key: int) -> bool:
    """
    Releases the previously acquired exclusive session-level advisory lock.
    Returns true if the lock is successfully released, or false if the lock was not held.
    """
    rows: Result = session.execute(text("SELECT pg_advisory_unlock(:lock_key)"), {"lock_key": lock_key})
    return next(rows)[0]


class BaseRepository:
    pass
