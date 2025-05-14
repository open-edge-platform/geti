// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

import { isEqual, isNil, negate } from 'lodash-es';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { MediaItem } from '../../../../core/media/media.interface';
import { isClassificationDomain } from '../../../../core/projects/domains';
import { AnnotationsMask } from '../../annotation/annotations-mask.component';
import { ShapeLabel } from '../../annotation/labels/shape-label.component';
import { Layer } from '../../annotation/layers/layer.component';
import { MediaImage } from '../../media-image.component';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { useAnnotatorCanvasSettings } from '../../providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component';
import {
    useExplanationOpacity,
    usePrediction,
} from '../../providers/prediction-provider/prediction-provider.component';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTaskChain } from '../../providers/task-chain-provider/task-chain-provider.component';
import { getGlobalAnnotations, getPreviousTask } from '../../providers/task-chain-provider/utils';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { filterForExplanation, filterForSelectedTask, filterHidden, isPredictionAnnotation } from '../../utils';
import { TransformZoomAnnotation } from '../../zoom/transform-zoom-annotation.component';
import { useZoom } from '../../zoom/zoom-provider.component';
import { ExplanationWithOpacity } from '../explanation/explanation.component';

import classes from './preview-canvas-content.module.scss';

interface PreviewCanvasContentProps {
    isPredictionMode: boolean;
    annotations: Annotation[];
    predictions: Annotation[];
    selectedMediaItem: MediaItem | undefined;
}

export const PreviewCanvasContent = ({
    annotations: initAnnotations,
    predictions,
    isPredictionMode,
    selectedMediaItem,
}: PreviewCanvasContentProps) => {
    const { image, roi } = useROI();
    const { inputs } = useTaskChain();
    const { zoomState } = useZoom();
    const { tasks, selectedTask } = useTask();
    const annotationToolContext = useAnnotationToolContext();
    const { canvasSettingsState } = useAnnotatorCanvasSettings();
    const { showOverlapAnnotations } = useExplanationOpacity();
    const { isExplanationVisible, selectedExplanation } = usePrediction();

    const isClassification = Boolean(selectedTask && isClassificationDomain(selectedTask.domain));

    const [canvasSettings] = canvasSettingsState;
    const maskedAnnotations = inputs.filter(({ isSelected }) => isSelected);
    const previousTask = getPreviousTask(tasks, selectedTask);
    const showMask = tasks.length > 1 && !isNil(previousTask);
    const annotations = !isEqual(predictions, initAnnotations)
        ? initAnnotations.filter(negate(isPredictionAnnotation))
        : [];

    const visibleAnnotations = (isPredictionMode ? predictions : annotations)
        .filter(filterHidden)
        .filter(filterForSelectedTask(selectedTask?.domain))
        .filter(filterForExplanation(selectedExplanation, isExplanationVisible));

    return (
        <div className={classes.previewContainer}>
            <TransformZoomAnnotation>
                <div
                    style={
                        {
                            '--zoom-level': zoomState.zoom,
                            strokeWidth: 'calc(2px / var(--zoom-level))',
                        } as CSSProperties
                    }
                >
                    <MediaImage image={image} selectedMediaItem={selectedMediaItem} />

                    <ExplanationWithOpacity explanation={selectedExplanation} enabled={isExplanationVisible} />

                    {showMask && (
                        <AnnotationsMask width={image.width} height={image.height} annotations={maskedAnnotations} />
                    )}

                    {showOverlapAnnotations && isClassification ? (
                        <></>
                    ) : (
                        <Layer
                            width={image.width}
                            height={image.height}
                            isPredictionMode={true}
                            annotations={visibleAnnotations}
                            hideLabels={Boolean(canvasSettings.hideLabels.value)}
                            selectedTask={selectedTask}
                            globalAnnotations={getGlobalAnnotations(visibleAnnotations, roi, selectedTask)}
                            removeBackground={showOverlapAnnotations}
                            renderLabel={(annotation) => (
                                <ShapeLabel
                                    showOptions={false}
                                    annotation={annotation}
                                    annotationToolContext={annotationToolContext}
                                />
                            )}
                        />
                    )}

                    {showOverlapAnnotations && (
                        <Layer
                            width={image.width}
                            height={image.height}
                            isPredictionMode={false}
                            annotations={annotations}
                            hideLabels={Boolean(canvasSettings.hideLabels.value)}
                            selectedTask={selectedTask}
                            globalAnnotations={getGlobalAnnotations(annotations, roi, selectedTask)}
                            isOverlap={!isClassification}
                            renderLabel={(annotation) => (
                                <ShapeLabel
                                    showOptions={false}
                                    annotation={annotation}
                                    annotationToolContext={annotationToolContext}
                                />
                            )}
                        />
                    )}
                </div>
            </TransformZoomAnnotation>
        </div>
    );
};
