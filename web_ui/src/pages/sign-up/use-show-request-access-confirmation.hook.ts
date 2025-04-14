// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
