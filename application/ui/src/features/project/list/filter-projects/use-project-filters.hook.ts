// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useMemo, useState } from 'react';

import { Project, TaskType } from '../../../../constants/shared-types';
import { filterProjects } from './utils';

interface UseProjectFiltersResult {
    searchName: string;
    setSearchName: (value: string) => void;
    selectedTaskTypes: TaskType[];
    setSelectedTaskTypes: (taskTypes: TaskType[]) => void;
    toggleTaskType: (taskType: TaskType) => void;
    filteredProjects: Project[];
    isFiltering: boolean;
}

export const useProjectFilters = (projects: Project[]): UseProjectFiltersResult => {
    const [searchName, setSearchName] = useState<string>('');
    const [selectedTaskTypes, setSelectedTaskTypes] = useState<TaskType[]>([]);

    const toggleTaskType = (taskType: TaskType) => {
        setSelectedTaskTypes((current) =>
            current.includes(taskType) ? current.filter((item) => item !== taskType) : [...current, taskType]
        );
    };

    const filteredProjects = useMemo(
        () => filterProjects(projects, searchName, selectedTaskTypes),
        [projects, searchName, selectedTaskTypes]
    );

    const isFiltering = searchName.trim() !== '' || selectedTaskTypes.length > 0;

    return {
        searchName,
        setSearchName,
        selectedTaskTypes,
        setSelectedTaskTypes,
        toggleTaskType,
        filteredProjects,
        isFiltering,
    };
};
