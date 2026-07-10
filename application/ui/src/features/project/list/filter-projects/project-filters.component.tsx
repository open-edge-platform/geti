// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { TaskType } from '@/api/types';
import { Checkbox, CheckboxGroup, SearchField } from '@geti-ui/ui';
import { isEmpty } from 'lodash-es';

import { FilterPopoverButton } from '../../../../components/filter-popover-button/filter-popover-button.component';
import { pluralize } from '../../../../shared/util';
import { MAP_PROJECT_TYPE_TO_TITLE } from '../util';
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
    const summary = isEmpty(selectedTaskTypes)
        ? null
        : `${selectedTaskTypes.length} ${pluralize(selectedTaskTypes.length, 'type', 'types')} selected`;

    return (
        <>
            <FilterPopoverButton
                ariaLabel={'Filter by task type'}
                placeholder={'Filter by task type'}
                summary={summary}
            >
                <CheckboxGroup
                    aria-label={'Filter by task type'}
                    value={selectedTaskTypes}
                    onChange={(values) => onSelectedTaskTypesChange(values as TaskType[])}
                >
                    {TASK_TYPE_OPTIONS.map((taskType) => (
                        <Checkbox key={taskType} value={taskType}>
                            {MAP_PROJECT_TYPE_TO_TITLE[taskType]}
                        </Checkbox>
                    ))}
                </CheckboxGroup>
            </FilterPopoverButton>

            <SearchField
                value={searchName}
                onChange={onSearchChange}
                placeholder={'Search by name...'}
                aria-label={'Search projects by name'}
                marginStart={'auto'}
            />
        </>
    );
};
