// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, View } from '@adobe/react-spectrum';
import { useNavigate } from 'react-router-dom';

import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { paths } from '../../../core/services/routes';
import { Header } from '../../shared/components/header/header.component';
import { useOrganization } from './hooks/organization.hook';
import { OrganizationServiceLimitsTable } from './organization-service-limits-table.component';

export const OrganizationServiceLimits = () => {
    const { FEATURE_FLAG_ORG_QUOTAS } = useFeatureFlags();
    const navigate = useNavigate();
    const { organization } = useOrganization();

    if (!FEATURE_FLAG_ORG_QUOTAS && organization) {
        navigate(paths.intelAdmin.organization.index({ organizationId: organization.id }));
    }

    return (
        <Flex direction={'column'}>
            <Header title={'Service limits'} />

            <View flex={1}>
                <OrganizationServiceLimitsTable />
            </View>
        </Flex>
    );
};
