// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { i18n } from '@/i18n';
import { isObject } from 'lodash-es';

/**
 * Wraps the error body of an `openapi-fetch` result (`{ detail }`) so it can be thrown.
 */
export class ApiError extends Error {
    readonly detail?: unknown;

    constructor(body: unknown) {
        const detail = isObject(body) && 'detail' in body ? body.detail : undefined;

        super(typeof detail === 'string' ? detail : i18n.t('application.notifications.unexpectedError'), {
            cause: body,
        });
        this.name = 'ApiError';
        this.detail = detail;
    }
}
