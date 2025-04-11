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

import { keepPreviousData, queryOptions, useQuery } from '@tanstack/react-query';
import { AuthContextProps } from 'react-oidc-context';

import { useApplicationServices } from '../../services/application-services-provider.component';
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
