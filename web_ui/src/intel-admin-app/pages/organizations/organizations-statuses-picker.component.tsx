// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Item, Key, Picker } from '@adobe/react-spectrum';

import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { AccountStatus } from '../../../core/organizations/organizations.interface';

export const ALL_ORGANIZATIONS = 'All';

type OrganizationStatuses = { name: AccountStatus | typeof ALL_ORGANIZATIONS };

export type OrganizationsStatusName = OrganizationStatuses[keyof OrganizationStatuses];

export const STATUSES: OrganizationStatuses[] = [
    { name: ALL_ORGANIZATIONS },
    { name: AccountStatus.ACTIVATED },
    { name: AccountStatus.INVITED },
    { name: AccountStatus.SUSPENDED },
    { name: AccountStatus.DELETED },
    { name: AccountStatus.REQUESTED_ACCESS },
];

interface OrganizationStatusesPickerProps {
    selectedOrgStatus: OrganizationsStatusName;
    onChangeSelectedOrgStatus: (status: OrganizationsStatusName) => void;
}

export const OrganizationsStatusesPicker: FC<OrganizationStatusesPickerProps> = ({
    selectedOrgStatus,
    onChangeSelectedOrgStatus,
}) => {
    const { FEATURE_FLAG_REQ_ACCESS } = useFeatureFlags();

    const handleChangedSelectedOrgStatus = (key: Key) => {
        const status = key as OrganizationsStatusName;

        onChangeSelectedOrgStatus(status);
    };

    return (
        <Picker
            selectedKey={selectedOrgStatus}
            items={STATUSES.filter(
                (status) => FEATURE_FLAG_REQ_ACCESS || status.name !== AccountStatus.REQUESTED_ACCESS
            )}
            onSelectionChange={handleChangedSelectedOrgStatus}
            aria-label={'Organizations status'}
            id={'organizations-filter-status-picker'}
        >
            {(status) => <Item key={status.name}>{status.name}</Item>}
        </Picker>
    );
};
