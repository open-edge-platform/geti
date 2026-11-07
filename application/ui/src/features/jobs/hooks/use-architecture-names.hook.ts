// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import type { ModelArchitecture, Project } from '@/api/types';
import { useQueries } from '@tanstack/react-query';

const toNamesMap = (results: { data?: { model_architectures: ModelArchitecture[] } }[]) => {
    const namesMap = new Map<string, string>();
    results.forEach(({ data }) => data?.model_architectures.forEach(({ id, name }) => namesMap.set(id, name)));

    return namesMap;
};

export const useArchitectureNames = (projects: Project[]): ((architectureId: string) => string) => {
    const taskTypes = Array.from(new Set(projects.map(({ task }) => task.task_type)));

    const names = useQueries({
        queries: taskTypes.map((task) =>
            $api.queryOptions(
                'get',
                '/api/model_architectures',
                { params: { query: { task } } },
                { staleTime: Infinity }
            )
        ),
        combine: toNamesMap,
    });

    return (architectureId: string) => names.get(architectureId) ?? architectureId;
};
