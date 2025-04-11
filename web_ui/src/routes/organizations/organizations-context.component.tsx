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

import isNil from 'lodash/isNil';

import { useFeatureFlags } from '../../core/feature-flags/hooks/use-feature-flags.hook';
import { useSelectedOrganization } from '../../core/organizations/hook/use-selected-organization.hook';
import { AccountStatus } from '../../core/organizations/organizations.interface';
import { useIsSaasEnv } from '../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { SuspendedOrganization } from '../../pages/errors/suspended-organization/suspended-organization.component';
import { CreditExhaustedModal } from './credit-exhausted-modal.component';
import { OrganizationSelectionModal } from './organization-selection-modal.component';

interface OrganizationsContextProps {
    children: ReactNode;
}

export const OrganizationsContext = ({ children }: OrganizationsContextProps): JSX.Element => {
    const isSaaS = useIsSaasEnv();
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();
    const { selectedOrganization, organizations, hasMultipleOrganizations, setSelectedOrganization } =
        useSelectedOrganization();

    if (hasMultipleOrganizations && isNil(selectedOrganization)) {
        return (
            <OrganizationSelectionModal
                title={'Select an organization'}
                organizations={organizations}
                onSelectedOrganization={setSelectedOrganization}
                description={'You belong to the following organizations.'}
            />
        );
    }

    if (isNil(selectedOrganization)) {
        // Loading indicator is rendered via Suspense
        return <></>;
    }

    if (hasMultipleOrganizations && selectedOrganization.status === AccountStatus.SUSPENDED) {
        return (
            <OrganizationSelectionModal
                title={`You no longer have access to Organization ${selectedOrganization.name}`}
                organizations={organizations}
                onSelectedOrganization={setSelectedOrganization}
                description={`You no longer have access to ${selectedOrganization.name}.`}
            />
        );
    }

    if (
        selectedOrganization.status === AccountStatus.DELETED ||
        selectedOrganization.status === AccountStatus.SUSPENDED
    ) {
        return <SuspendedOrganization status={selectedOrganization.status} />;
    }

    return (
        <>
            {children}
            {FEATURE_FLAG_CREDIT_SYSTEM && isSaaS && <CreditExhaustedModal organizationId={selectedOrganization.id} />}
        </>
    );
};
