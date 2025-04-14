// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
