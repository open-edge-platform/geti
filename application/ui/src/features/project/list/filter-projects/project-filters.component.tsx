// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { TaskType } from '@/api/types';
import { useTranslation } from '@/i18n';
import { Checkbox, CheckboxGroup, Flex, SearchField } from '@geti-ui/ui';

import { MAP_PROJECT_TYPE_TO_TITLE_KEY } from '../util';
import { TASK_TYPE_OPTIONS } from './utils';

import classes from './project-filters.module.scss';

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

    return (
        <Flex direction={'column'} gap={'size-300'}>
            <SearchField
                width={'100%'}
                value={searchName}
                onChange={onSearchChange}
                placeholder={t('project.list.filters.searchPlaceholder')}
                aria-label={'Search projects by name'}
            />

            <CheckboxGroup
                label={t('project.list.filters.taskType')}
                value={selectedTaskTypes}
                onChange={(values) => onSelectedTaskTypesChange(values as TaskType[])}
                UNSAFE_className={classes.taskTypeFilter}
            >
                {TASK_TYPE_OPTIONS.map((taskType) => (
                    <Checkbox key={taskType} value={taskType}>
                        {t(MAP_PROJECT_TYPE_TO_TITLE_KEY[taskType])}
                    </Checkbox>
                ))}
            </CheckboxGroup>
        </Flex>
    );
};
