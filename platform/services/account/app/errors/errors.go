// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package account_service

const (
	ErrCodeNotFound        = "NOT_FOUND"
	ErrCodeInvalidRequest  = "INVALID_REQUEST"
	ErrCodeInternal        = "INTERNAL"
	ErrCodeConflict        = "CONFLICT"
	ErrCodeUnknown         = "UNKNOWN"
	ErrCodeAleardyExists   = "ALREADY_EXISTS"
	ErrCodeUnauthenticated = "UNAUTHENTICATED"
)

type BaseError struct {
	Code    string
	Message string
}

func (e *BaseError) Error() string {
	return e.Message
}

type InvalidRequestError struct {
	BaseError
}

func NewInvalidReuestError(message string) *InvalidRequestError {
	return &InvalidRequestError{
		BaseError: BaseError{
			Code:    ErrCodeInvalidRequest,
			Message: message,
		},
	}
}

type ConflictError struct {
	BaseError
}

func NewConflictError(message string) *ConflictError {
	return &ConflictError{
		BaseError: BaseError{
			Code:    ErrCodeConflict,
			Message: message,
		},
	}
}

type NotFoundError struct {
	BaseError
}

func NewNotFoundError(message string) *NotFoundError {
	return &NotFoundError{
		BaseError: BaseError{
			Code:    ErrCodeNotFound,
			Message: message,
		},
	}
}

type UnknownError struct {
	BaseError
}

func NewUnknownError(message string) *UnknownError {
	return &UnknownError{
		BaseError: BaseError{
			Code:    ErrCodeUnknown,
			Message: message,
		},
	}
}

type UnauthenticatedError struct {
	BaseError
}

func NewUnauthenticatedError(message string) *UnauthenticatedError {
	return &UnauthenticatedError{
		BaseError: BaseError{
			Code:    ErrCodeUnauthenticated,
			Message: message,
		},
	}
}

type InternalError struct {
	BaseError
}

func NewInternalError(message string) *InternalError {
	return &InternalError{
		BaseError: BaseError{
			Code:    ErrCodeInternal,
			Message: message,
		},
	}
}


type DatabaseError struct {
    BaseError
}

func NewDatabaseError(message string, code string) *DatabaseError {
	return &DatabaseError{
		BaseError: BaseError{
			Code:    code,
			Message: message,
        },
    }
}
