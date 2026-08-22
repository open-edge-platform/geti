// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Project } from '@/api/types';
import { orderBy } from 'lodash-es';

export const SORT_BY_OPTIONS = [
    [
        { nameKey: 'projectList.sortNameAscending', key: 'name-ascending' },
        { nameKey: 'projectList.sortNameDescending', key: 'name-descending' },
    ],
    [
        { nameKey: 'projectList.sortCreatedAtNewest', key: 'createdAt-descending' },
        { nameKey: 'projectList.sortCreatedAtOldest', key: 'createdAt-ascending' },
    ],
] as const;

export type SortBy = (typeof SORT_BY_OPTIONS)[number][number]['key'];

export const SORT_BY_HANDLERS: Record<SortBy, (projects: Project[]) => Project[]> = {
    'name-ascending': (projects) => orderBy(projects, (project) => project.name.toLocaleLowerCase(), 'asc'),
    'name-descending': (projects) => orderBy(projects, (project) => project.name.toLocaleLowerCase(), 'desc'),
    'createdAt-ascending': (projects) => orderBy(projects, (project) => project.created_at, 'asc'),
    'createdAt-descending': (projects) => orderBy(projects, (project) => project.created_at, 'desc'),
};
