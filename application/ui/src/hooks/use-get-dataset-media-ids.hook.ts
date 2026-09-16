// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { fetchClient } from '@/api';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { buildDatasetMediaQueryFilters, UseGetDatasetMediaItemsOptions } from './use-get-dataset-media-items.hook';

export const useGetDatasetMediaIds = () => {
    const project_id = useProjectIdentifier();

    const fetchDatasetMediaIds = async (options?: UseGetDatasetMediaItemsOptions) => {
        const query = buildDatasetMediaQueryFilters(options);

        const response = await fetchClient.GET('/api/projects/{project_id}/dataset/media/ids', {
            params: {
                path: { project_id },
                query,
            },
        });

        return response.data?.items.map((item) => item.id) ?? [];
    };

    return fetchDatasetMediaIds;
};
