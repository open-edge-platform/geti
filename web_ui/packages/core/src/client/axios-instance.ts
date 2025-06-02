// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import axios, { AxiosError, isCancel } from 'axios';

import { CSRF_HEADERS } from '../services/security';
import { getErrorMessageByStatusCode } from '../services/utils';

/*
    Axios instance used for Intel® Geti™ requests
*/

export const apiClient = axios.create({
    withCredentials: true,
    headers: { ...CSRF_HEADERS },
});

apiClient.interceptors.response.use(
    (response) => {
        return response;
    },
    (error: AxiosError) => {
        // Throttling user canceled requests to prevent error panel popup
        if (isCancel(error)) return Promise.resolve({ data: {} });

        (error as AxiosError).message = getErrorMessageByStatusCode(error);

        return Promise.reject(error);
    }
);
