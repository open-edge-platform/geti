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

import { useAuth } from 'react-oidc-context';

import { useLogoutMutation } from '../../core/auth/hooks/use-logout-mutation.hook';
import { paths } from '../../core/services/routes';
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
