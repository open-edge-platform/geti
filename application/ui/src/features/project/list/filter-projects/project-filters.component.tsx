// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { TaskType } from '@/api/types';
import { Checkbox, CheckboxGroup, Flex, SearchField, View } from '@geti-ui/ui';
import { isEmpty } from 'lodash-es';
import { useTranslation } from 'react-i18next';

import { FilterPopoverButton } from '../../../../components/filter-popover-button/filter-popover-button.component';
import { getTaskTypeTitle } from '../util';
import { TASK_TYPE_OPTIONS } from './utils';

type ProjectFiltersProps = {
    searchName: string;
    onSearchChange: (value: string) => void;
    selectedTaskTypes: TaskType[];
    onSelectedTaskTypesChange: (taskTypes: TaskType[]) => void;
};

export const ProjectFilters = ({
    searchName,
    onSearchChange,
    selectedTaskTypes,
    onSelectedTaskTypesChange,
}: ProjectFiltersProps) => {
    const { t } = useTranslation();

    const summary = isEmpty(selectedTaskTypes)
        ? null
        : t('projectList.typesSelected', { count: selectedTaskTypes.length });

    return (
        <Flex alignItems={'center'} gap={'size-200'} flex={1}>
            <SearchField
                value={searchName}
                onChange={onSearchChange}
                placeholder={t('projectList.searchByNamePlaceholder')}
                aria-label={t('projectList.searchByNameAriaLabel')}
                flex={1}
            />

            <View backgroundColor={'gray-50'}>
                <FilterPopoverButton
                    ariaLabel={t('projectList.filterByTaskType')}
                    placeholder={t('projectList.filterByTaskType')}
                    summary={summary}
                    minWidth={'size-2400'}
                    dialogWidth={'size-1600'}
                >
                    <CheckboxGroup
                        aria-label={t('projectList.filterByTaskType')}
                        value={selectedTaskTypes}
                        onChange={(values) => onSelectedTaskTypesChange(values as TaskType[])}
                    >
                        {TASK_TYPE_OPTIONS.map((taskType) => (
                            <Checkbox key={taskType} value={taskType}>
                                {getTaskTypeTitle(taskType)}
                            </Checkbox>
                        ))}
                    </CheckboxGroup>
                </FilterPopoverButton>
            </View>
        </Flex>
    );
};
