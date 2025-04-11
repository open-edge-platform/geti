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

import { useUsers } from '../../core/users/hook/use-users.hook';
import { User } from '../../core/users/users.interface';
import { useIsSaasEnv } from '../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { useOrganizationIdentifier } from '../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { formatDate } from '../utils';

interface UsePreviousSignIn {
    lastLoginDate: string | null;
    userId: string | undefined;
}

export const usePreviousSignIn = (): UsePreviousSignIn => {
    const isSaaS = useIsSaasEnv();
    const { organizationId } = useOrganizationIdentifier();
    const { useActiveUser } = useUsers();
    const { data: activeUser, isSuccess } = useActiveUser(organizationId);
    const lastSuccessfulLogin = (activeUser as User)?.lastSuccessfulLogin;
    const hasValidLoginDate = isSuccess && isSaaS && lastSuccessfulLogin;

    if (hasValidLoginDate) {
        const lastLoginDate = !isSaaS ? '' : formatDate(lastSuccessfulLogin, 'DD MMM YYYY, HH:mm:ss');

        return { lastLoginDate, userId: (activeUser as User).id };
    }

    return { lastLoginDate: null, userId: undefined };
};
