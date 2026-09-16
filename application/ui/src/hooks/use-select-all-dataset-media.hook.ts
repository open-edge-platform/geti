// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { fetchClient } from '@/api';
import { useMutation } from '@tanstack/react-query';
import { omit } from 'lodash-es';

import { useDatasetMediaFilterOptions } from './use-dataset-media-filter-options.hook';
import { buildDatasetMediaQueryFilters } from './use-get-dataset-media-items.hook';
import { useProjectIdentifier } from './use-project-identifier.hook';

export const useSelectAllDatasetMedia = () => {
    const projectId = useProjectIdentifier();
    const filterOptions = useDatasetMediaFilterOptions();

    return useMutation({
        mutationFn: async () => {
            // Sorting is meaningless for an unordered set of ids, and the endpoint does not accept it.
            const query = omit(buildDatasetMediaQueryFilters(filterOptions), ['sort_by', 'sort_direction']);

            const { data, error, response } = await fetchClient.GET('/api/projects/{project_id}/dataset/media/ids', {
                params: { path: { project_id: projectId }, query },
            });

            if (error !== undefined || data === undefined) {
                throw new Error(`Failed to select all media: ${response.status} ${response.statusText}`);
            }

            return {
                mediaIds: data.items.map(({ id }) => id),
                imageIds: data.items.filter(({ type }) => type === 'image').map(({ id }) => id),
            };
        },
    });
};
