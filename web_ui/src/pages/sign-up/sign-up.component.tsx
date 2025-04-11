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

import { ReactNode } from 'react';

import { Navigate } from 'react-router-dom';

import { useFeatureFlags } from '../../core/feature-flags/hooks/use-feature-flags.hook';
import { paths } from '../../core/services/routes';
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
