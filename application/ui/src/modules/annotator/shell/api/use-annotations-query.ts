// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ApiError, fetchClient } from '@/api';
import type { AnnotationDTO, DatasetSubset, Media } from '@/api/types';
import { queryOptions, useQuery, type QueryKey } from '@tanstack/react-query';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { isEmpty, isObject } from 'lodash-es';

import { getQueryKey } from '../../../../query-client/query-client';
import { EMPTY_LABEL_ID } from '../../../../shared/labels';
import { getMediaItemQueryParams } from '../../../../shared/media-item-utils';

const isUnannotatedError = (error: unknown): boolean => {
    return isObject(error) && 'detail' in error && /Media has not been annotated yet/i.test(String(error.detail));
};

const getAnnotationsQueryKey = (projectId: string, media: Media): QueryKey => {
    return getQueryKey([
        'get',
        `/api/projects/{project_id}/dataset/media/{media_id}/annotations`,
        {
            params: {
                path: { project_id: projectId, media_id: media.id },
                query: getMediaItemQueryParams(media),
            },
        },
    ]);
};

export const annotationsQueryOptions = (projectId: string, media: Media) =>
    queryOptions({
        queryKey: getAnnotationsQueryKey(projectId, media),
        queryFn: () => annotationsQueryFn(projectId, media),
        // Saving annotations invalidates this query, so revisiting a media item can be served from the cache
        staleTime: 1000 * 60,
    });

const isValidAnnotation = (annotation: AnnotationDTO): boolean => {
    if (annotation.shape.type === 'polygon' && isEmpty(annotation.shape.points)) {
        return false;
    }

    return true;
};

const annotationsQueryFn = async (
    projectId: string,
    media: Media
): Promise<{ annotations: AnnotationDTO[]; user_reviewed: boolean; subset: DatasetSubset }> => {
    const queryParams = getMediaItemQueryParams(media);

    const { data, error, response } = await fetchClient.GET(
        '/api/projects/{project_id}/dataset/media/{media_id}/annotations',
        {
            params: {
                path: {
                    project_id: projectId,
                    media_id: media.id,
                },
                query: queryParams,
            },
        }
    );

    if (isUnannotatedError(error) || response.status === 404) {
        return { annotations: [], user_reviewed: false, subset: 'unassigned' };
    }

    if (error) {
        throw new ApiError(error);
    }

    if (data == undefined) {
        throw new ApiError({ detail: `No data returned from API for media ${media.id}` });
    }

    if (data.annotations.length === 0) {
        const annotationDTO = {
            shape: {
                type: 'full_image',
            },
            labels: [{ id: EMPTY_LABEL_ID }],
        } satisfies AnnotationDTO;

        return {
            annotations: [annotationDTO],
            user_reviewed: true,
            subset: data.subset,
        };
    }

    return {
        ...data,
        annotations: data.annotations.filter(isValidAnnotation),
    };
};

export const useAnnotationsQuery = (media: Media) => {
    const projectId = useProjectIdentifier();

    return useQuery(annotationsQueryOptions(projectId, media));
};
