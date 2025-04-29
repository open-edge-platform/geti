// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ValidationError } from 'yup';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const isYupValidationError = (error: any): error is ValidationError => {
    return error.name === 'ValidationError' && error.message;
};
