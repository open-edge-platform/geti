// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Project } from '@/api/types';
import { orderBy } from 'lodash-es';

export const SORT_BY_OPTIONS = [
    [
        { nameKey: 'nameAZ', key: 'name-ascending' },
        { nameKey: 'nameZA', key: 'name-descending' },
    ],
    [
        { nameKey: 'createdNewest', key: 'createdAt-descending' },
        { nameKey: 'createdOldest', key: 'createdAt-ascending' },
    ],
] as const;

export type SortBy = (typeof SORT_BY_OPTIONS)[number][number]['key'];

export const SORT_BY_HANDLERS: Record<SortBy, (projects: Project[]) => Project[]> = {
    'name-ascending': (projects) => orderBy(projects, (project) => project.name.toLocaleLowerCase(), 'asc'),
    'name-descending': (projects) => orderBy(projects, (project) => project.name.toLocaleLowerCase(), 'desc'),
    'createdAt-ascending': (projects) => orderBy(projects, (project) => project.created_at, 'asc'),
    'createdAt-descending': (projects) => orderBy(projects, (project) => project.created_at, 'desc'),
};
