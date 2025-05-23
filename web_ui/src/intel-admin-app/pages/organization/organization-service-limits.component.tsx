// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core/src/services/routes';
import { Flex, View } from '@geti/ui';
import { useNavigate } from 'react-router-dom';

import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
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
