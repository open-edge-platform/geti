# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Custom exceptions"""


class NoDatabaseResult(Exception):
    """Raised when the database doesn't contain the requested object"""


class SubscriptionExistsException(Exception):
    """Raised when an organization tries to create a subscription which already exists"""


class ServiceException(Exception):
    """Base exception for errors inside service classes"""


class InvalidStateTransitionException(Exception):
    """Raised when status transition of a state machine is not a valid one"""


class TransactionException(ServiceException):
    """Base transaction exception used for errors while performing transaction operations"""


class InsufficientBalanceException(TransactionException):
    def __init__(self, balance: int, required: int):
        message = f"Not enough credits to create a lease: {balance} available, {required} required."
        super().__init__(message)
        self.balance = balance
        self.required = required
