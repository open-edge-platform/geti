// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { instance as defaultAxiosInstance } from '../../services/axios-instance';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { AuthService } from './auth-service.interface';

export const createApiAuthService: CreateApiService<AuthService> = (
    { instance, router } = { instance: defaultAxiosInstance, router: API_URLS }
) => {
    const login: AuthService['login'] = async (authToken) => {
        return await instance.post(router.AUTH_COOKIE, undefined, {
            headers: {
                Authorization: `Bearer ${authToken}`,
            },
        });
    };

    const logout: AuthService['logout'] = async () => {
        localStorage.clear();

        await instance.post(router.LOGOUT);
    };

    return {
        login,
        logout,
    };
};
