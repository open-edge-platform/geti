// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction, useState } from 'react';

import { Flex, SearchField } from '@geti/ui';

import { GetOrganizationsQueryOptions } from '../../../core/organizations/services/organizations-service.interface';
import { useDebouncedCallback } from '../../../hooks/use-debounced-callback/use-debounced-callback.hook';
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
