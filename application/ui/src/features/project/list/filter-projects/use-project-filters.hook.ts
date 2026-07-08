// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useMemo, useState } from 'react';

import { Project } from '../../../../constants/shared-types';
import { filterProjects, TaskCategory } from './utils';

interface UseProjectFiltersResult {
    searchName: string;
    setSearchName: (value: string) => void;
    selectedCategories: TaskCategory[];
    setSelectedCategories: (categories: TaskCategory[]) => void;
    toggleCategory: (category: TaskCategory) => void;
    filteredProjects: Project[];
    isFiltering: boolean;
}

export const useProjectFilters = (projects: Project[]): UseProjectFiltersResult => {
    const [searchName, setSearchName] = useState<string>('');
    const [selectedCategories, setSelectedCategories] = useState<TaskCategory[]>([]);

    const toggleCategory = (category: TaskCategory) => {
        setSelectedCategories((current) =>
            current.includes(category)
                ? current.filter((item) => item !== category)
                : [...current, category]
        );
    };

    const filteredProjects = useMemo(
        () => filterProjects(projects, searchName, selectedCategories),
        [projects, searchName, selectedCategories]
    );

    const isFiltering = searchName.trim() !== '' || selectedCategories.length > 0;

    return {
        searchName,
        setSearchName,
        selectedCategories,
        setSelectedCategories,
        toggleCategory,
        filteredProjects,
        isFiltering,
    };
};
