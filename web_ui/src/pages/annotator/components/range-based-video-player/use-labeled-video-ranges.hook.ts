// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect, useRef } from 'react';

import { useMutation, UseMutationResult, useQuery, useQueryClient, UseQueryResult } from '@tanstack/react-query';
import isEmpty from 'lodash/isEmpty';

import { LabeledVideoRange } from '../../../../core/annotations/labeled-video-range.interface';
import { Label } from '../../../../core/labels/label.interface';
import { Video } from '../../../../core/media/video.interface';
import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import QUERY_KEYS from '../../../../core/requests/query-keys';
import { useApplicationServices } from '../../../../core/services/application-services-provider.component';

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
