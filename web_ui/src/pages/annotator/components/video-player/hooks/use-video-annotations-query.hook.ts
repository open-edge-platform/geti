// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect, useRef } from 'react';

import { useQuery } from '@tanstack/react-query';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { VideoPaginationOptions } from '../../../../../core/annotations/services/video-pagination-options.interface';
import { Video } from '../../../../../core/media/video.interface';
import { DatasetIdentifier } from '../../../../../core/projects/dataset.interface';
import QUERY_KEYS from '../../../../../core/requests/query-keys';
import { useApplicationServices } from '../../../../../core/services/application-services-provider.component';
import { useProject } from '../../../../project-details/providers/project-provider/project-provider.component';

export const useVideoAnnotationsQueryOptions = (datasetIdentifier: DatasetIdentifier) => {
    const { annotationService } = useApplicationServices();
    const { project } = useProject();
    return (video: Video, options: VideoPaginationOptions) => {
        const videoAnnotationsQueryKey = [
            ...QUERY_KEYS.VIDEO_ANNOTATIONS(datasetIdentifier, video.identifier, options),
        ];
        return {
            queryKey: videoAnnotationsQueryKey,
            queryFn: () => {
                return annotationService.getVideoAnnotations(datasetIdentifier, project.labels, video, options);
            },
            // Make sure that the options' range contains at least 1 valid frame
            enabled: options.startFrame >= 0 && options.startFrame < video.metadata.frames,
            refetchOnMount: false,
            // We want to manually clear the video annotations cache when the user switches to a different video
            cacheTime: Infinity,
            staleTime: Infinity,
            meta: { disableGlobalErrorHandling: true },
        };
    };
};

export const useVideoAnnotationsQuery = <T>(
    datasetIdentifier: DatasetIdentifier,
    video: Video,
    select: (data: Record<number, Annotation[]>) => T,
    options: VideoPaginationOptions,
    enabled = true,
    onSuccess?: (x: T) => void
) => {
    const getQueryOptions = useVideoAnnotationsQueryOptions(datasetIdentifier);
    const queryOptions = getQueryOptions(video, options);
    const handleSuccessRef = useRef(onSuccess);

    const isQueryEnabled = enabled && queryOptions.enabled;

    const query = useQuery({
        ...queryOptions,
        enabled: isQueryEnabled,
        select,
    });

    useEffect(() => {
        handleSuccessRef.current = onSuccess;
    }, [onSuccess]);

    useEffect(() => {
        if (!isQueryEnabled || !query.isSuccess) {
            return;
        }

        handleSuccessRef.current?.(query.data);
    }, [isQueryEnabled, query.isSuccess, query.data]);

    return query;
};
