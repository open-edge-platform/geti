// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import axios, { AxiosError, isCancel } from 'axios';

import { LOCAL_STORAGE_KEYS } from '../../shared/local-storage-keys';
import { removeLocalStorageKey } from '../../shared/utils';
import { CSRF_HEADERS } from './security';
import { getErrorMessageByStatusCode, isAuthenticationResponseUrl } from './utils';

/*
    Axios instance used for Intel® Geti™ requests
*/

export const instance = axios.create({
    withCredentials: true,
    headers: { ...CSRF_HEADERS },
});

instance.interceptors.response.use(
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
