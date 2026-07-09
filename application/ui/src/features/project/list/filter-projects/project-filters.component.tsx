// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Flex, SearchField, SearchFieldProps, ToggleButton } from '@geti-ui/ui';

import { TaskType } from '../../../../constants/shared-types';
import { MAP_PROJECT_TYPE_TO_TITLE } from '../util';
import { TASK_TYPE_COLORS, TASK_TYPE_OPTIONS } from './utils';

import classes from './project-filters.module.scss';

type ProjectFiltersProps = {
    searchName: string;
    onSearchChange: (value: string) => void;
    selectedTaskTypes: TaskType[];
    onToggleTaskType: (taskType: TaskType) => void;
    searchWidth?: SearchFieldProps['width'];
};

export const ProjectFilters = ({
    searchName,
    onSearchChange,
    selectedTaskTypes,
    onToggleTaskType,
    searchWidth = { base: '100%', M: 'size-3000' },
}: ProjectFiltersProps) => {
    return (
        <Flex gap={'size-100'} alignItems={'center'} wrap>
            <SearchField
                value={searchName}
                onChange={onSearchChange}
                placeholder={'Search by name...'}
                aria-label={'Search projects by name'}
                width={searchWidth}
            />

            <Flex gap={'size-75'} alignItems={'center'} wrap>
                {TASK_TYPE_OPTIONS.map((taskType) => (
                    <ToggleButton
                        key={taskType}
                        isQuiet
                        isSelected={selectedTaskTypes.includes(taskType)}
                        onChange={() => onToggleTaskType(taskType)}
                        UNSAFE_className={classes.taskButton}
                        aria-label={`Filter by ${MAP_PROJECT_TYPE_TO_TITLE[taskType]}`}
                    >
                        <span style={{ color: TASK_TYPE_COLORS[taskType] }}>{MAP_PROJECT_TYPE_TO_TITLE[taskType]}</span>
                    </ToggleButton>
                ))}
            </Flex>
        </Flex>
    );
};
