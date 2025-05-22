// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import axios, { AxiosError, isCancel } from 'axios';

import { CSRF_HEADERS } from '../../../../src/core/services/security';
import { getErrorMessageByStatusCode, isAuthenticationResponseUrl } from '../../../../src/core/services/utils';
import { LOCAL_STORAGE_KEYS } from '../../../../src/shared/local-storage-keys';
import { removeLocalStorageKey } from '../../../../src/shared/utils';

/*
    Axios instance used for Intel® Geti™ requests
*/

export const apiClient = axios.create({
    withCredentials: true,
    headers: { ...CSRF_HEADERS },
});

apiClient.interceptors.response.use(
    (response) => {
        if (isAuthenticationResponseUrl(response)) {
            localStorage.setItem(LOCAL_STORAGE_KEYS.UNAUTHORIZED, 'true');
            window.dispatchEvent(new Event('storage'));

            return Promise.reject(response);
        } else {
            removeLocalStorageKey(LOCAL_STORAGE_KEYS.UNAUTHORIZED);
        }

        return response;
    },
    (error: AxiosError) => {
        // Throttling user canceled requests to prevent error panel popup
        if (isCancel(error)) return Promise.resolve({ data: {} });

        (error as AxiosError).message = getErrorMessageByStatusCode(error);

        return Promise.reject(error);
    }
);
