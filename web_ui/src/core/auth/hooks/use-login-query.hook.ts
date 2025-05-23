// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { keepPreviousData, queryOptions, useQuery } from '@tanstack/react-query';
import { AuthContextProps } from 'react-oidc-context';

import { AuthService } from '../services/auth-service.interface';

const loginQueryOptions = (authService: AuthService, idToken: string | undefined) => {
    return queryOptions({
        queryKey: ['user-login-token', idToken],
        queryFn: async () => {
            if (idToken === undefined) {
                throw new Error('ID Token is undefined');
            }

            await authService.login(idToken);

            return null;
        },
        enabled: idToken !== undefined,
        // This makes it so that the query's loading property will be false while we are
        // fetching the cookie for a new idToken
        placeholderData: keepPreviousData,
        throwOnError: false,
        retry: false,
    });
};

export const useLoginQuery = (auth: AuthContextProps) => {
    const { authService } = useApplicationServices();

    const idToken = auth.user?.id_token;

    return useQuery(loginQueryOptions(authService, idToken));
};
