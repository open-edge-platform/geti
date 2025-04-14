// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { VideoFrame } from '../../../../core/media/video.interface';
import { isClassificationDomain } from '../../../../core/projects/domains';
import { useStreamingVideoPlayer } from '../../components/video-player/streaming-video-player/streaming-video-player-provider.component';
import { useVideoStreamingAnnotations } from '../../components/video-player/streaming-video-player/use-video-streaming-annotations.hook';
import { getAdjustedNeighbourSize } from '../../components/video-player/streaming-video-player/utils';
import { ANNOTATOR_MODE } from '../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { useExplanationOpacity } from '../../providers/prediction-provider/prediction-provider.component';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { getGlobalAnnotations } from '../../providers/task-chain-provider/utils';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { ShapeLabel } from '../labels/shape-label.component';
import { Layer } from './layer.component';
import { LayersProps } from './utils';

export interface VideoLayersProps extends LayersProps {
    selectedMediaItem: VideoFrame;
}

export const VideoLayers = ({
    selectedMediaItem,
    annotationsFilter,
    annotations: _noVideoAnnotations,
    ...props
}: VideoLayersProps) => {
    const { tasks, selectedTask } = useTask();
    const task = selectedTask ?? tasks[0];

    const { roi } = useROI();
    const videoPlayerContext = useStreamingVideoPlayer();
    const isClassification = isClassificationDomain(task.domain);
    const { isActiveLearningMode } = useAnnotatorMode();
    const { showOverlapAnnotations } = useExplanationOpacity();

    const { currentIndex, neighbourSize, playbackRate } = videoPlayerContext;
    const predictionModeShowsAnnotations = !isActiveLearningMode && showOverlapAnnotations;

    const adjustedNeighbourSize = getAdjustedNeighbourSize(selectedMediaItem.metadata.fps, playbackRate, neighbourSize);

    const annotations =
        useVideoStreamingAnnotations(
            selectedMediaItem,
            currentIndex,
            adjustedNeighbourSize,
            ANNOTATOR_MODE.ACTIVE_LEARNING
        ) ?? [];

    const predictions =
        useVideoStreamingAnnotations(
            selectedMediaItem,
            currentIndex,
            adjustedNeighbourSize,
            ANNOTATOR_MODE.PREDICTION
        ) ?? [];

    const filteredPredictions = annotationsFilter(predictions);
    const filteredAnnotations = annotationsFilter(annotations);

    const annotationsByMode = isActiveLearningMode ? filteredAnnotations : filteredPredictions;

    return (
        <>
            {predictionModeShowsAnnotations && isClassification ? (
                <></>
            ) : (
                <Layer
                    {...props}
                    selectedTask={selectedTask}
                    annotations={annotationsByMode}
                    isPredictionMode={!isActiveLearningMode}
                    globalAnnotations={getGlobalAnnotations(annotationsByMode, roi, task)}
                    renderLabel={(annotation) => (
                        <ShapeLabel
                            showOptions={isActiveLearningMode}
                            annotation={annotation}
                            areLabelsInteractive={props.areLabelsInteractive}
                            annotationToolContext={props.annotationToolContext}
                        />
                    )}
                />
            )}

            {predictionModeShowsAnnotations && (
                <Layer
                    {...props}
                    isOverlap={!isClassification}
                    isPredictionMode={false}
                    selectedTask={selectedTask}
                    globalAnnotations={getGlobalAnnotations(filteredAnnotations, roi, task)}
                    annotations={filteredAnnotations}
                    renderLabel={(annotation) => (
                        <ShapeLabel
                            showOptions={false}
                            annotation={annotation}
                            areLabelsInteractive={props.areLabelsInteractive}
                            annotationToolContext={props.annotationToolContext}
                        />
                    )}
                />
            )}
        </>
    );
};
