// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
