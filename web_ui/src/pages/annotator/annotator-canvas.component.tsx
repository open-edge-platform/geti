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

import { MouseEvent, useRef } from 'react';

import isNil from 'lodash/isNil';

import { isExclusive } from '../../core/labels/utils';
import { MediaItem } from '../../core/media/media.interface';
import { isClassificationDomain } from '../../core/projects/domains';
import { isKeypointTask } from '../../core/projects/utils';
import { AnnotationsMask } from './annotation/annotations-mask.component';
import { Labels } from './annotation/labels/labels.component';
import { LayersFactory } from './annotation/layers/layers-factory.component';
import { ExplanationWithOpacity } from './components/explanation/explanation.component';
import { AnnotationToolContext, ToolType } from './core/annotation-tool-context.interface';
import { useAnnotatorMode } from './hooks/use-annotator-mode';
import { useIsSceneBusy } from './hooks/use-annotator-scene-interaction-state.hook';
import { useVisibleAnnotations } from './hooks/use-visible-annotations.hook';
import { MediaImage } from './media-image.component';
import { useAnnotatorCanvasSettings } from './providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component';
import { AnnotationContextMenu } from './providers/annotator-context-menu-provider/annotation-context-menu.component';
import { AnnotatorContextMenuProvider } from './providers/annotator-context-menu-provider/annotator-context-menu-provider.component';
import { usePrediction } from './providers/prediction-provider/prediction-provider.component';
import { useROI } from './providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTaskChain } from './providers/task-chain-provider/task-chain-provider.component';
import { getPreviousTask } from './providers/task-chain-provider/utils';
import { useTask } from './providers/task-provider/task-provider.component';
import { CanvasTools } from './tools/canvas-tools.component';
import { EditTool } from './tools/edit-tool/edit-tool.component';
import { EraserTool } from './tools/eraser-tool/eraser-tool.component';
import { useIsSelectionToolActive } from './tools/selecting-tool/selecting-state-provider.component';
import { SelectingToolType } from './tools/selecting-tool/selecting-tool.enums';
import { filterIfInEditMode } from './utils';

import classes from './annotator-canvas.module.scss';

interface AnnotatorCanvasProps {
    selectedMediaItem: MediaItem | undefined;
    annotationToolContext: AnnotationToolContext;
    canEditAnnotationLabel: boolean;
}

export function AnnotatorCanvas({
    selectedMediaItem,
    annotationToolContext,
    canEditAnnotationLabel,
}: AnnotatorCanvasProps): JSX.Element {
    const { image } = useROI();
    const { tasks, selectedTask } = useTask();
    const { tool } = annotationToolContext;

    const isBusy = useIsSceneBusy();
    const { inputs } = useTaskChain();
    const { isActiveLearningMode } = useAnnotatorMode();
    const canvasRef = useRef<SVGSVGElement>(null);
    const containerCanvasRef = useRef<HTMLDivElement>(null);
    const previousTask = getPreviousTask(tasks, selectedTask);
    const { isExplanationVisible, selectedExplanation } = usePrediction();

    const showMask: boolean = tasks.length > 1 && !isNil(previousTask);
    const maskedAnnotations = inputs.filter(({ isSelected }) => isSelected);
    const isSelectionToolEnabled = tool === ToolType.SelectTool;
    const explanationEnabled = tool === ToolType.Explanation && isExplanationVisible && !isBusy;

    const isBrushToolActive = useIsSelectionToolActive(SelectingToolType.BrushTool);
    const isStampToolActive = useIsSelectionToolActive(SelectingToolType.StampTool);

    const visibleAnnotations = useVisibleAnnotations();
    const selectedAnnotations = visibleAnnotations.filter(({ isSelected, isLocked }) => isSelected && !isLocked);

    // If the user uses the selection tool then we want the selection tool to be responsible for rendering the selected
    // annotations. If there is only one selected annotation, the edition tool is responsible for rendering the selected
    // annotation. This makes it so that we can perform some performance improvements when the user drags one or
    // multiple annotations.
    const isInEditMode = selectedAnnotations.length === 1 && !isStampToolActive;
    const isMultipleSelection = isSelectionToolEnabled && selectedAnnotations.length > 1;

    const annotations = isMultipleSelection
        ? visibleAnnotations.filter(({ isSelected }) => !isSelected)
        : visibleAnnotations.filter(filterIfInEditMode(isInEditMode));

    const { canvasSettingsState } = useAnnotatorCanvasSettings();
    const [canvasSettings] = canvasSettingsState;

    const hasKeypointTasks = tasks.some(isKeypointTask);
    const isDisabledTranslation = !isSelectionToolEnabled || (isSelectionToolEnabled && isStampToolActive);

    const isAnomalyOrClassificationProject = (): boolean => {
        if (!selectedTask) return false;

        const { domain } = selectedTask;

        return isClassificationDomain(domain);
    };

    const handleContextMenu = (event: MouseEvent): void => {
        return event.preventDefault();
    };

    const isAnnotationContextMenuEnabled =
        !isBusy && isSelectionToolEnabled && !isBrushToolActive && !isAnomalyOrClassificationProject();

    return (
        <div
            ref={containerCanvasRef}
            className={classes.canvas}
            onContextMenu={handleContextMenu}
            aria-label='Annotator canvas'
        >
            <AnnotatorContextMenuProvider>
                {isAnnotationContextMenuEnabled && (
                    <AnnotationContextMenu
                        annotations={visibleAnnotations}
                        containerCanvasRef={containerCanvasRef}
                        annotationToolContext={annotationToolContext}
                        disableAnnotationContextMenu={!hasKeypointTasks}
                    />
                )}

                <MediaImage image={image} selectedMediaItem={selectedMediaItem} />
                {isAnomalyOrClassificationProject() ? (
                    <>
                        {showMask && (
                            <AnnotationsMask
                                width={image.width}
                                height={image.height}
                                annotations={visibleAnnotations}
                            />
                        )}

                        <LayersFactory
                            width={image.width}
                            height={image.height}
                            annotations={visibleAnnotations}
                            areLabelsInteractive={!isStampToolActive}
                            annotationToolContext={annotationToolContext}
                            canEditAnnotationLabel={canEditAnnotationLabel}
                        />
                    </>
                ) : (
                    <>
                        <LayersFactory
                            width={image.width}
                            height={image.height}
                            annotations={isActiveLearningMode ? annotations : visibleAnnotations}
                            annotationToolContext={annotationToolContext}
                            areLabelsInteractive={!isStampToolActive}
                            hideLabels={
                                Boolean(canvasSettings.hideLabels.value) || canvasSettings.labelOpacity.value === 0
                            }
                            canEditAnnotationLabel={canEditAnnotationLabel}
                        />

                        {showMask && (
                            <AnnotationsMask
                                width={image.width}
                                height={image.height}
                                annotations={maskedAnnotations}
                            />
                        )}

                        {maskedAnnotations
                            .filter(({ labels: iLabels }) => iLabels.some(isExclusive))
                            .map((annotation) => (
                                <Labels
                                    key={annotation.id}
                                    annotation={annotation}
                                    annotationToolContext={annotationToolContext}
                                    canEditAnnotationLabel={canEditAnnotationLabel}
                                />
                            ))}

                        {!isBusy && (
                            <svg
                                ref={canvasRef}
                                id={'annotations-canvas-tools'}
                                className={classes.layer}
                                width={image.width}
                                height={image.height}
                            >
                                <EraserTool
                                    canvasRef={canvasRef}
                                    scene={annotationToolContext.scene}
                                    annotations={annotations}
                                >
                                    <CanvasTools annotationToolContext={annotationToolContext} />
                                </EraserTool>
                            </svg>
                        )}

                        {isActiveLearningMode && isInEditMode ? (
                            <EditTool
                                annotationToolContext={annotationToolContext}
                                disableTranslation={isDisabledTranslation}
                                canvasRef={canvasRef}
                            />
                        ) : (
                            <></>
                        )}
                    </>
                )}

                <ExplanationWithOpacity explanation={selectedExplanation} enabled={explanationEnabled} />
            </AnnotatorContextMenuProvider>
        </div>
    );
}
