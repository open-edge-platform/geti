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

import { useEffect, useState } from 'react';

import { hasAuthParams, useAuth } from 'react-oidc-context';
import { Outlet, useLocation, useSearchParams } from 'react-router-dom';
import { useLocalStorage } from 'usehooks-ts';

import { useLoginQuery } from '../../core/auth/hooks/use-login-query.hook';
import { LoginErrorScreen } from '../../pages/errors/login-error/login-error-screen.component';
import { IntelBrandedLoading } from '../../shared/components/loading/intel-branded-loading.component';
import { LOCAL_STORAGE_KEYS } from '../../shared/local-storage-keys';

const useOnboardingTokenSearchParam = (): string | null => {
    const [searchParams] = useSearchParams();
    const onboardingToken = searchParams.get('signup-token');

    return onboardingToken;
};

export const AuthenticationLayout = (): JSX.Element => {
    const auth = useAuth();
    const [userIsLoggedIn, setIsUserLoggedIn] = useState(false);
    const onboardingToken = useOnboardingTokenSearchParam();

    const location = useLocation();
    const setRedirectLocation = useLocalStorage(
        LOCAL_STORAGE_KEYS.INTENDED_PATH_BEFORE_AUTHENTICATION,
        location.pathname
    )[1];

    // If the user's access token has expired then this likely means that they have a refresh token
    // that has expired as well.
    useEffect(() => {
        if (auth.user && auth.user.expired && !auth.isLoading) {
            auth.removeUser();
        }
    }, [auth]);

    const loginQuery = useLoginQuery(auth);

    useEffect(() => {
        const shouldAttemptLogin =
            auth &&
            !hasAuthParams() &&
            !auth.isAuthenticated &&
            !auth.activeNavigator &&
            !auth.isLoading &&
            !userIsLoggedIn;

        // what about the case when user is authenticated but didn't finish the registration?

        if (shouldAttemptLogin) {
            setRedirectLocation(location.pathname);

            onboardingToken === null
                ? auth.signinRedirect()
                : auth.signinRedirect({
                      url_state: onboardingToken,
                  });

            setIsUserLoggedIn(true);
        }
    }, [auth, userIsLoggedIn, location.pathname, setRedirectLocation, onboardingToken]);

    if (!auth) {
        return <Outlet />;
    }

    if (auth.isLoading || auth.activeNavigator || loginQuery.isPending) {
        return <IntelBrandedLoading />;
    }

    return <>{auth?.error || loginQuery.isError ? <LoginErrorScreen /> : <Outlet />}</>;
};
