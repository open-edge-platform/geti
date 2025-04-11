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
