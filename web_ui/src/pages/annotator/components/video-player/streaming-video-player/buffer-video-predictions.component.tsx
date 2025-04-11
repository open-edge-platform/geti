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

import { useEffect } from 'react';

import { useQuery } from '@tanstack/react-query';

import { PredictionMode } from '../../../../../core/annotations/services/prediction-service.interface';
import { MEDIA_TYPE } from '../../../../../core/media/base-media.interface';
import { VideoFrame, Video as VideoInterface } from '../../../../../core/media/video.interface';
import { ANNOTATOR_MODE } from '../../../core/annotation-tool-context.interface';
import { useDatasetIdentifier } from '../../../hooks/use-dataset-identifier.hook';
import { useInferenceServerStatus } from '../../../providers/prediction-provider/use-inference-server-status';
import { useVideoAnnotationsQueryOptions } from '../hooks/use-video-annotations-query.hook';
import { useVideoPredictionsQueryOptions } from '../hooks/use-video-predictions-query.hook';
import { Buffer } from './utils';

const useQueryNextBuffer = (nextBuffer: Buffer, mode: ANNOTATOR_MODE, video: VideoInterface) => {
    const isActiveLearningMode = mode === ANNOTATOR_MODE.ACTIVE_LEARNING;

    const datasetIdentifier = useDatasetIdentifier();
    const annotationsQueryOptions = useVideoAnnotationsQueryOptions(datasetIdentifier);
    const predictionsQueryOptions = useVideoPredictionsQueryOptions(datasetIdentifier, PredictionMode.ONLINE);

    const options = {
        startFrame: nextBuffer.startFrame,
        endFrame: nextBuffer.endFrame,
        frameSkip: nextBuffer.frameSkip,
    };

    const queryOptions = isActiveLearningMode
        ? annotationsQueryOptions(video, options)
        : predictionsQueryOptions(video, options);

    // We disable the prediction queries if the inference server isn't ready yet
    const { data = { isInferenceServerReady: false } } = useInferenceServerStatus(datasetIdentifier, true);
    const enabled = queryOptions?.enabled && (isActiveLearningMode || data.isInferenceServerReady);

    return useQuery({ ...queryOptions, enabled });
};

interface BufferVideoPredictionsProps {
    mode: ANNOTATOR_MODE;
    nextBuffer: Buffer;
    videoFrame: VideoFrame;
    setBuffers: (buffers: Buffer[]) => void;
}

export const BufferVideoPredictions = ({ nextBuffer, setBuffers, videoFrame, mode }: BufferVideoPredictionsProps) => {
    const video = {
        ...videoFrame,
        identifier: {
            type: MEDIA_TYPE.VIDEO as const,
            videoId: videoFrame.identifier.videoId,
        },
    };

    const query = useQueryNextBuffer(nextBuffer, mode, video);

    useEffect(() => {
        // This is a bit of an hack: we update the buffers so that the system rerenders and then
        // decides the next buffer to load
        setBuffers([]);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [query.status]);

    return <></>;
};
