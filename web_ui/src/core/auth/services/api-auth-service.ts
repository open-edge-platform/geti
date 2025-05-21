// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { client } from '@geti/core';

import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { AuthService } from './auth-service.interface';

export const createApiAuthService: CreateApiService<AuthService> = (
    { instance, router } = { instance: client, router: API_URLS }
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
