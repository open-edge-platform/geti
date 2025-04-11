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

import { UseQueryResult } from '@tanstack/react-query';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { PredictionMode } from '../../../../../core/annotations/services/prediction-service.interface';
import { MEDIA_TYPE } from '../../../../../core/media/base-media.interface';
import { Video } from '../../../../../core/media/video.interface';
import { getIds } from '../../../../../shared/utils';
import { useDatasetIdentifier } from '../../../hooks/use-dataset-identifier.hook';
import { getVideoOptions } from '../streaming-video-player/utils';
import { useVideoPlayer } from '../video-player-provider.component';
import { useVideoAnnotationsQuery } from './use-video-annotations-query.hook';
import { useVideoPredictionsQuery } from './use-video-predictions-query.hook';

const selectLabelsOfFrame = (frameNumber: number) => {
    return (data: Record<number, ReadonlyArray<Annotation>>) => {
        if (data[frameNumber]) {
            const annotations = data[Number(frameNumber)];
            const labelIds = annotations.flatMap(({ labels }) => getIds(labels));
            return new Set<string>(labelIds);
        }

        return new Set<string>();
    };
};

interface UseVideoEditor {
    annotationsQuery: UseQueryResult<Set<string>>;
    predictionsQuery: UseQueryResult<Set<string>>;
}

const TIMELINE_VIDEO_FRAMES_CHUNK_SIZE = 20;
// This hook returns annotations and predictions queries that load a chunk of frames,
// while using the `select` option so that consumers of this hook only get the annotations
// and predictions associatd to the given frame number.
// This makes it so that we can request annotations and predictions for 1 frame, while caching
// the data for any neighbouring frames
export const useVideoTimelineQueries = (frameNumber: number): UseVideoEditor => {
    // TODO: this can change if the user changes the selected dataset, which will
    // introduce a bug
    const datasetIdentifier = useDatasetIdentifier();
    const { videoFrame, step } = useVideoPlayer();

    const video: Video = {
        ...videoFrame,
        identifier: { type: MEDIA_TYPE.VIDEO, videoId: videoFrame.identifier.videoId },
    };

    const options = getVideoOptions(video, frameNumber, step, TIMELINE_VIDEO_FRAMES_CHUNK_SIZE);

    const annotationsQuery = useVideoAnnotationsQuery(
        datasetIdentifier,
        video,
        selectLabelsOfFrame(frameNumber),
        options
    );
    const predictionsQuery = useVideoPredictionsQuery(
        datasetIdentifier,
        video,
        selectLabelsOfFrame(frameNumber),
        options,
        PredictionMode.LATEST
    );

    return { annotationsQuery, predictionsQuery };
};
