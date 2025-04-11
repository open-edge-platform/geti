// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useQueryClient } from '@tanstack/react-query';
import isEmpty from 'lodash/isEmpty';
import sortBy from 'lodash/sortBy';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { Explanation } from '../../../../core/annotations/prediction.interface';
import { PredictionMode } from '../../../../core/annotations/services/prediction-service.interface';
import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { isVideoFrame } from '../../../../core/media/video.interface';
import QUERY_KEYS from '../../../../core/requests/query-keys';
import { useDatasetIdentifier } from '../../hooks/use-dataset-identifier.hook';
import { useSelectedMediaItem } from '../selected-media-item-provider/selected-media-item-provider.component';
import { updateVideoTimelineQuery } from '../selected-media-item-provider/utils';
import { useTask } from '../task-provider/task-provider.component';

export const minimalThresholdPercentage = (annotations: ReadonlyArray<Annotation>): number => {
    const scores = annotations.flatMap(({ labels }) => {
        return labels.map((label) => label.score ?? 1.0);
    });

    return isEmpty(scores) ? 0 : Math.round(100 * Math.min(...scores));
};

export const useUpdateVideoPredictionsTimeline = () => {
    const { selectedTask } = useTask();
    const queryClient = useQueryClient();
    const datasetIdentifier = useDatasetIdentifier();
    const { selectedMediaItem } = useSelectedMediaItem();

    return (annotations: ReadonlyArray<Annotation>) => {
        if (selectedMediaItem !== undefined && isVideoFrame(selectedMediaItem) && !isEmpty(annotations)) {
            const videoTimelineQueryKeyPrefix = QUERY_KEYS.VIDEO_PREDICTIONS(
                datasetIdentifier,
                {
                    type: MEDIA_TYPE.VIDEO,
                    videoId: selectedMediaItem.identifier.videoId,
                },
                PredictionMode.LATEST,
                selectedTask
            );

            updateVideoTimelineQuery(queryClient, videoTimelineQueryKeyPrefix, selectedMediaItem, annotations);
        }
    };
};

export const sortExplanationsByName = (maps: Explanation[] = []) => sortBy(maps, (m) => m.name);

export const selectFirstOrNoneFromList = (list: Explanation[]): Explanation | undefined =>
    list.length >= 1 ? list[0] : undefined;
