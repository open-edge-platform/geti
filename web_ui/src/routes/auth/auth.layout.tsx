// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

import { IntelBrandedLoading } from '@geti/ui';
import { hasAuthParams, useAuth } from 'react-oidc-context';
import { Outlet, useLocation, useSearchParams } from 'react-router-dom';
import { useLocalStorage } from 'usehooks-ts';

import { useLoginQuery } from '../../core/auth/hooks/use-login-query.hook';
import { LoginErrorScreen } from '../../pages/errors/login-error/login-error-screen.component';
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
