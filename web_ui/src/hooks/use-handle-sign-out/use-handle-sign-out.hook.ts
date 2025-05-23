// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core/src/services/routes';
import { useAuth } from 'react-oidc-context';

import { useLogoutMutation } from '../../core/auth/hooks/use-logout-mutation.hook';
import { redirectTo } from '../../shared/utils';
import { clearAllStorage } from '../use-clear-indexeddb-storage/use-clear-indexeddb-storage.hook';

const handleSignOut = (): void => {
    const url = `${paths.signOut({})}?rd=${window.location.origin}${paths.signOutPage({})}`;

    redirectTo(encodeURI(url));
};

export const useHandleSignOut = () => {
    const auth = useAuth();
    const logout = useLogoutMutation();

    const idToken = auth.user?.id_token;

    if (auth) {
        return () => {
            logout.mutateAsync().finally(() => {
                clearAllStorage();
                auth.signoutRedirect({ id_token_hint: idToken });
            });
        };
    }

    // NOTE: currently we only sign out the user by redirecting them, in the future once
    // we've implemented oauth we will need access to an AuthProvider to sign out a user
    return handleSignOut;
};
