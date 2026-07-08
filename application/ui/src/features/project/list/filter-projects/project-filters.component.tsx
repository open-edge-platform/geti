// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Flex, SearchField, ToggleButton } from '@geti-ui/ui';

import { TASK_CATEGORY_COLORS, TASK_CATEGORY_LABELS, TASK_CATEGORY_OPTIONS, TaskCategory } from './utils';

import classes from './project-filters.module.scss';

interface ProjectFiltersProps {
    searchName: string;
    onSearchChange: (value: string) => void;
    selectedCategories: TaskCategory[];
    onToggleCategory: (category: TaskCategory) => void;
    searchWidth?: string;
}

export const ProjectFilters = ({
    searchName,
    onSearchChange,
    selectedCategories,
    onToggleCategory,
    searchWidth = 'size-3000',
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
                {TASK_CATEGORY_OPTIONS.map((category) => (
                    <ToggleButton
                        key={category}
                        isQuiet
                        isSelected={selectedCategories.includes(category)}
                        onChange={() => onToggleCategory(category)}
                        aria-label={`Filter by ${TASK_CATEGORY_LABELS[category]}`}
                    >
                        <span
                            className={classes.categoryDot}
                            style={{ backgroundColor: TASK_CATEGORY_COLORS[category] }}
                        />
                        {TASK_CATEGORY_LABELS[category]}
                    </ToggleButton>
                ))}
            </Flex>
        </Flex>
    );
};
