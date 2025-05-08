// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useEffect, useMemo } from 'react';

import { isEqual, isNil } from 'lodash-es';

import { getShapesBoundingBox } from '../../../core/annotations/math';
import { useAnnotationScene } from '../providers/annotation-scene-provider/annotation-scene-provider.component';
import { useSelectedMediaItem } from '../providers/selected-media-item-provider/selected-media-item-provider.component';
import { getInputForTask } from '../providers/task-chain-provider/utils';
import { useTask } from '../providers/task-provider/task-provider.component';
import { useZoom, ZoomTarget } from './zoom-provider.component';

export const useZoomIntoAnnotation = (): void => {
    const { setZoomTarget, zoomTarget } = useZoom();
    const { selectedMediaItem } = useSelectedMediaItem();
    const { tasks, selectedTask, previousTask } = useTask();
    const { annotations } = useAnnotationScene();

    const taskAnnotations = getInputForTask(annotations, tasks, selectedTask);

    const selectedAnnotations = useMemo(
        () => taskAnnotations.filter(({ isSelected }) => isSelected),
        [taskAnnotations]
    );

    const zoomIntoAnnotation = useCallback(() => {
        // Suppose we are in a Detection -> Classification or Detection -> Segmentation task, then
        // we want to zoom into selected annotations if the user selected the Classification,
        // or Segmentation tasks
        const shapes = selectedAnnotations.map(({ shape }) => shape);

        // If there are no previous annotations, there is nothing to zoom into
        if (!shapes.length) {
            return;
        }

        const boundingBox = getShapesBoundingBox(shapes);

        setZoomTarget((oldTarget) => {
            return isEqual(oldTarget, boundingBox) ? oldTarget : boundingBox;
        });
    }, [selectedAnnotations, setZoomTarget]);

    const resetZoom = useCallback(() => {
        if (!selectedMediaItem) {
            return;
        }

        const { width, height } = selectedMediaItem.image;

        // Initially the zoomTarget is the image target, so before we actually reset the state
        // We need to compare the image target (which is the initial target) with the current zoomTarget
        const imageTargetConfig = { x: 0, y: 0, width, height } as ZoomTarget;

        const targetChanged = !isEqual(imageTargetConfig, zoomTarget);

        if (targetChanged) {
            setZoomTarget(imageTargetConfig);
        }
    }, [zoomTarget, selectedMediaItem, setZoomTarget]);

    // If the user changes to from a global to a local task we zoom into the annotation
    // Otherwise we reset the zoomTarget
    useEffect(() => {
        const previousTaskWasLocalTask = !isNil(previousTask) || (isNil(previousTask) && tasks.length === 2);

        if (previousTaskWasLocalTask && selectedAnnotations.length) {
            zoomIntoAnnotation();
        } else {
            resetZoom();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [previousTask, selectedAnnotations.length, tasks.length, zoomIntoAnnotation]);
};
