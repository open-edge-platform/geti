// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { paths } from '@geti/core';
import { Navigate } from 'react-router-dom';

import { useFeatureFlags } from '../../core/feature-flags/hooks/use-feature-flags.hook';
import { useProfileQuery } from '../../core/users/hook/use-profile.hook';
import { useIsSaasEnv } from '../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { SignUpOnSaas } from './sign-up-on-saas.component';
import { useShowRequestAccessConfirmation } from './use-show-request-access-confirmation.hook';

export const SignUp = ({ children }: { children: ReactNode }) => {
    const isSaasEnv = useIsSaasEnv();
    const { data: profileData } = useProfileQuery();
    const { FEATURE_FLAG_USER_ONBOARDING } = useFeatureFlags();

    const showRequestedAccess = useShowRequestAccessConfirmation();

    if (showRequestedAccess) {
        return <Navigate to={paths.requestedAccess({})} replace />;
    }

    if (!isSaasEnv || !FEATURE_FLAG_USER_ONBOARDING || profileData?.hasAcceptedUserTermsAndConditions === true) {
        return <>{children}</>;
    }

    return <SignUpOnSaas />;
};
