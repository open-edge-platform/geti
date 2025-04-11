// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useFeatureFlags } from '../../core/feature-flags/hooks/use-feature-flags.hook';
import { AccountStatus } from '../../core/organizations/organizations.interface';
import { useProfileQuery } from '../../core/users/hook/use-profile.hook';
import { useIsSaasEnv } from '../../hooks/use-is-saas-env/use-is-saas-env.hook';

export const useShowRequestAccessConfirmation = (): boolean => {
    const isSassEnv = useIsSaasEnv();
    const { data } = useProfileQuery();
    const { FEATURE_FLAG_USER_ONBOARDING, FEATURE_FLAG_REQ_ACCESS } = useFeatureFlags();

    const showRequestAccessConfirmation =
        isSassEnv &&
        FEATURE_FLAG_USER_ONBOARDING &&
        FEATURE_FLAG_REQ_ACCESS &&
        data.organizations.at(0)?.userStatus === AccountStatus.REQUESTED_ACCESS;

    return showRequestAccessConfirmation;
};
