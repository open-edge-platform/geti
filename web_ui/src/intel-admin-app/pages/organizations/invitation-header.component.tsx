// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps } from 'react';

import { Flex } from '@geti/ui';

import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { GenerateOnboardingTokenDialogContainer } from './generate-onboarding-invitation-link-dialog/generate-onboarding-invitation-link-dialog.component';
import { InviteOrganization } from './invite-organization.component';

export const InvitationHeader = ({
    organizationsQueryOptions,
}: ComponentProps<typeof InviteOrganization>): JSX.Element => {
    const { FEATURE_FLAG_FREE_TIER, FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK } = useFeatureFlags();
    return (
        <Flex alignItems={'center'} gap={'size-100'}>
            <InviteOrganization organizationsQueryOptions={organizationsQueryOptions} />
            {FEATURE_FLAG_FREE_TIER && FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK && (
                <GenerateOnboardingTokenDialogContainer />
            )}
        </Flex>
    );
};
