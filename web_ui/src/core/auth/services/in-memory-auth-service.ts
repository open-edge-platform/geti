// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AuthService } from './auth-service.interface';

export const createInMemoryAuthService = (): AuthService => {
    const login = async () => {
        return;
    };
    const logout = async () => {
        return;
    };

    return {
        login,
        logout,
    };
};
