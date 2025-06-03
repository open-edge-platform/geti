// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AxiosError } from 'axios';

export interface IntervalJobHandlers<T> {
    onError?: (error: AxiosError) => void;
    onSuccess?: (data: T) => void;
    onSettled?: (data: T) => void;
    onCancelOrFailed?: () => void;
    onCancel?: () => void;
}
