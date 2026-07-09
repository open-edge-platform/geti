// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Flex, SearchField, Text, ToggleButton } from '@geti-ui/ui';

import { TaskType } from '../../../../constants/shared-types';
import { MAP_PROJECT_TYPE_TO_TITLE } from '../util';
import { TASK_TYPE_COLORS, TASK_TYPE_OPTIONS } from './utils';

type ProjectFiltersProps = {
    searchName: string;
    onSearchChange: (value: string) => void;
    selectedTaskTypes: TaskType[];
    onToggleTaskType: (taskType: TaskType) => void;
};

export const ProjectFilters = ({
    searchName,
    onSearchChange,
    selectedTaskTypes,
    onToggleTaskType,
}: ProjectFiltersProps) => {
    return (
        <>
            <Flex gap={'size-75'} alignItems={'center'}>
                {TASK_TYPE_OPTIONS.map((taskType) => (
                    <ToggleButton
                        key={taskType}
                        isQuiet
                        isSelected={selectedTaskTypes.includes(taskType)}
                        onChange={() => onToggleTaskType(taskType)}
                        aria-label={`Filter by ${MAP_PROJECT_TYPE_TO_TITLE[taskType]}`}
                    >
                        <Text UNSAFE_style={{ color: TASK_TYPE_COLORS[taskType] }}>
                            {MAP_PROJECT_TYPE_TO_TITLE[taskType]}
                        </Text>
                    </ToggleButton>
                ))}
            </Flex>

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
