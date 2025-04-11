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

import negate from 'lodash/negate';

import { Annotation as AnnotationInterface } from '../../../../core/annotations/annotation.interface';
import { isVideoFrame } from '../../../../core/media/video.interface';
import { isClassificationDomain } from '../../../../core/projects/domains';
import { useStreamingVideoPlayer } from '../../components/video-player/streaming-video-player/streaming-video-player-provider.component';
import { useIsPredictionRejected } from '../../providers/annotation-threshold-provider/annotation-threshold-provider.component';
import { usePrediction } from '../../providers/prediction-provider/prediction-provider.component';
import { useSelectedMediaItem } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { Layers } from './layers.component';
import { filterByExplanationSelection, isExplanationSelected, LayersProps } from './utils';
import { VideoLayers } from './video-layers.component';

export const LayersFactory = (props: Omit<LayersProps, 'annotationsFilter'>) => {
    const { tasks, selectedTask } = useTask();
    const task = selectedTask ?? tasks[0];

    const { isPlaying } = useStreamingVideoPlayer();
    const { selectedMediaItem } = useSelectedMediaItem();
    const isClassification = isClassificationDomain(task.domain);
    const { selectedExplanation, isExplanationVisible } = usePrediction();

    const isPredictionRejected = useIsPredictionRejected();
    const isPredictionAccepted = negate(isPredictionRejected);

    const annotationsFilter = (
        annotations: AnnotationInterface[],
        extraFilter: (a: AnnotationInterface) => boolean = () => true
    ) => {
        const filteredByExplanation = isExplanationSelected(isExplanationVisible, selectedExplanation)
            ? filterByExplanationSelection(annotations, isClassification, selectedExplanation)
            : annotations;

        return filteredByExplanation.filter(
            (annotation) => isPredictionAccepted(annotation) && extraFilter(annotation)
        );
    };

    if (isPlaying && isVideoFrame(selectedMediaItem)) {
        return <VideoLayers {...props} selectedMediaItem={selectedMediaItem} annotationsFilter={annotationsFilter} />;
    }

    return <Layers {...props} annotationsFilter={annotationsFilter} />;
};
