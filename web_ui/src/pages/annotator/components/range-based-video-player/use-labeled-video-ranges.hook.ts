// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useMutation, UseMutationResult, useQuery, useQueryClient, UseQueryResult } from '@tanstack/react-query';
import { isEmpty } from 'lodash-es';

import { LabeledVideoRange } from '../../../../core/annotations/labeled-video-range.interface';
import { Label } from '../../../../core/labels/label.interface';
import { Video } from '../../../../core/media/video.interface';
import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import QUERY_KEYS from '../../../../core/requests/query-keys';

export const useLabeledVideoRangesQuery = (
    datasetIdentifier: DatasetIdentifier,
    mediaItem: Video,
    labels: Label[],
    onSuccess: (ranges: LabeledVideoRange[]) => void
): UseQueryResult<LabeledVideoRange[]> => {
    const { annotationService } = useApplicationServices();
    const handleSuccessRef = useRef(onSuccess);

    const query = useQuery({
        queryKey: QUERY_KEYS.VIDEO_RANGE_ANNOTATIONS(datasetIdentifier, mediaItem.identifier),
        queryFn: () => {
            return annotationService.getLabeledVideoRanges(datasetIdentifier, mediaItem, labels);
        },
    });

    useEffect(() => {
        handleSuccessRef.current = onSuccess;
    }, [onSuccess]);

    useEffect(() => {
        if (!query.isSuccess || isEmpty(query.data)) {
            return;
        }

        handleSuccessRef.current(query.data);
    }, [query.isSuccess, query.data]);

    return query;
};

export const useLabeledVideoRangesMutation = (
    datasetIdentifier: DatasetIdentifier,
    mediaItem: Video
): UseMutationResult<void, unknown, LabeledVideoRange[]> => {
    const { annotationService } = useApplicationServices();
    const client = useQueryClient();

    return useMutation({
        mutationFn: async (ranges: LabeledVideoRange[]) => {
            return annotationService.saveLabeledVideoRanges(datasetIdentifier, mediaItem, ranges);
        },
        onSuccess: () => {
            client.invalidateQueries({ queryKey: QUERY_KEYS.ADVANCED_MEDIA_ITEMS(datasetIdentifier, {}, {}) });
        },
    });
};
