// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useRef } from 'react';

import { fetchClient } from '@/api';
import { i18n } from '@/i18n';
import { useMutation } from '@tanstack/react-query';
import { isEqual, omit } from 'lodash-es';

import { useDatasetMediaFilterOptions } from './use-dataset-media-filter-options.hook';
import { buildDatasetMediaQueryFilters } from './use-get-dataset-media-items.hook';
import { useProjectIdentifier } from './use-project-identifier.hook';

export const useSelectAllDatasetMedia = () => {
    const projectId = useProjectIdentifier();
    const filterOptions = useDatasetMediaFilterOptions();

    // Sorting is meaningless for an unordered set of ids, and the endpoint does not accept it.
    const query = omit(buildDatasetMediaQueryFilters(filterOptions), ['sort_by', 'sort_direction']);

    // The mutation callback closes over the filters of the render it was called in, so the latest
    // ones have to be reachable through a ref to detect that they changed mid-request.
    const latestQuery = useRef(query);
    latestQuery.current = query;

    return useMutation({
        mutationFn: async () => {
            const requestedQuery = latestQuery.current;

            const { data, error } = await fetchClient.GET('/api/projects/{project_id}/dataset/media/ids', {
                params: { path: { project_id: projectId }, query: requestedQuery },
            });

            if (error !== undefined || data === undefined) {
                throw error ?? new Error(i18n.t('application.notifications.unexpectedError'));
            }

            // The filters changed mid-request, so these ids no longer describe what the gallery
            // shows. `null` tells the caller to discard them instead of selecting hidden media.
            if (!isEqual(requestedQuery, latestQuery.current)) {
                return null;
            }

            return {
                mediaIds: data.items.map(({ id }) => id),
                imageIds: data.items.filter(({ type }) => type === 'image').map(({ id }) => id),
            };
        },
    });
};
