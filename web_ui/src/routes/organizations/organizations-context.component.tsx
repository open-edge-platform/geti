// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
