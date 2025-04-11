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

import { ComponentProps } from 'react';

import { Flex } from '@adobe/react-spectrum';

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
