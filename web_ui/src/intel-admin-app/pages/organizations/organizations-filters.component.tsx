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

import { Dispatch, SetStateAction, useState } from 'react';

import { Flex } from '@adobe/react-spectrum';

import { GetOrganizationsQueryOptions } from '../../../core/organizations/services/organizations-service.interface';
import { useDebouncedCallback } from '../../../hooks/use-debounced-callback/use-debounced-callback.hook';
import { SearchField } from '../../../shared/components/search-field/search-field.component';
import { EntitiesCounter } from '../../shared/components/entities-counter/entities-counter.component';
import {
    ALL_ORGANIZATIONS,
    OrganizationsStatusesPicker,
    STATUSES,
    type OrganizationsStatusName,
} from './organizations-statuses-picker.component';

interface OrganizationsFiltersProps {
    totalCount: number;
    totalMatchedCount: number;
    hasFilters: boolean;
    setOrganizationsQueryOptions: Dispatch<SetStateAction<GetOrganizationsQueryOptions>>;
}

export const OrganizationsFilters = ({
    totalCount,
    hasFilters,
    totalMatchedCount,
    setOrganizationsQueryOptions,
}: OrganizationsFiltersProps): JSX.Element => {
    const [filterByOrganizationName, setFilterByOrganizationName] = useState<string>('');
    const [selectedOrgStatus, setSelectedOrgStatus] = useState<OrganizationsStatusName>(STATUSES[0].name);

    const debouncedFilterByOrgNameCallback = useDebouncedCallback((orgName) => {
        setOrganizationsQueryOptions((prevState) => {
            const newState = { ...prevState };

            if (orgName === '') {
                delete newState.name;

                return newState;
            }

            return { ...prevState, name: orgName };
        });
    }, 300);

    const handleOrgNameChange = (name: string): void => {
        setFilterByOrganizationName(name);

        debouncedFilterByOrgNameCallback(name);
    };

    const handleOrgStatusChange = (status: OrganizationsStatusName): void => {
        setSelectedOrgStatus(status);

        if (status === ALL_ORGANIZATIONS) {
            setOrganizationsQueryOptions((prevState) => {
                const newState = { ...prevState };

                delete newState.status;

                return newState;
            });

            return;
        }

        setOrganizationsQueryOptions((prevState) => ({ ...prevState, status }));
    };

    return (
        <Flex alignItems={'center'} gap={'size-200'}>
            <Flex alignItems={'center'} marginY={'size-200'} gap={'size-200'}>
                <SearchField
                    isQuiet={false}
                    width={'size-3400'}
                    aria-label={'Search by name or email'}
                    placeholder={'Search by name or email'}
                    value={filterByOrganizationName}
                    onChange={handleOrgNameChange}
                />

                <OrganizationsStatusesPicker
                    selectedOrgStatus={selectedOrgStatus}
                    onChangeSelectedOrgStatus={handleOrgStatusChange}
                />
            </Flex>
            {totalCount > 0 && (
                <EntitiesCounter
                    totalMatchedCount={totalMatchedCount}
                    totalCount={totalCount}
                    hasFilters={hasFilters}
                    entity={'organization'}
                />
            )}
        </Flex>
    );
};
