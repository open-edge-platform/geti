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

import isEmpty from 'lodash/isEmpty';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { Explanation } from '../../../../core/annotations/prediction.interface';
import { isGlobal } from '../../../../core/labels/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { isDetectionDomain, isRotatedDetectionDomain, isSegmentationDomain } from '../../../../core/projects/domains';
import { hasEqualId } from '../../../../shared/utils';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { GrabcutToolType } from '../../tools/grabcut-tool/grabcut-tool.enums';
import { PolygonMode } from '../../tools/polygon-tool/polygon-tool.enum';
import { SelectingToolType } from '../../tools/selecting-tool/selecting-tool.enums';
import { hasEmptyLabels } from '../../utils';

export const EMPTY_ANNOTATIONS: ReadonlyArray<Annotation> = [];
export const EMPTY_EXPLANATION: Explanation[] = [];

export type HotKeyActions =
    | ToolType
    | GrabcutToolType
    | SelectingToolType
    | PolygonMode.MagneticLasso
    | 'saveAnnotations'
    | 'delete'
    | 'deleteSecond'
    | 'selectAll'
    | 'deselectAll'
    | 'undo'
    | 'redo'
    | 'redoSecond'
    | 'playOrPause'
    | 'nextFrame'
    | 'previousFrame'
    | 'next'
    | 'previous'
    | 'zoom'
    | 'imageDrag'
    | 'imageDragSecond'
    | 'copyAnnotation'
    | 'pasteAnnotation'
    | 'close'
    | 'accept'
    | 'hideAllAnnotations';

export type Hotkeys = Record<HotKeyActions, string>;

export const DefaultHotkeys = (
    prefix: 'meta' | 'ctrl'
): Omit<Hotkeys, GrabcutToolType | SelectingToolType | PolygonMode.MagneticLasso> => ({
    saveAnnotations: `${prefix}+s`,
    delete: 'delete',
    deleteSecond: 'backspace',
    selectAll: `${prefix}+a`,
    deselectAll: `${prefix}+d`,
    undo: `${prefix}+z`,
    redo: `${prefix}+y`,
    redoSecond: `${prefix}+shift+z`,
    playOrPause: 'k',
    nextFrame: 'right',
    previousFrame: 'left',
    next: 'arrowright',
    previous: 'arrowleft',
    zoom: `${prefix}+f`,
    imageDrag: `${prefix}+drag`,
    imageDragSecond: 'mouse middle click',
    copyAnnotation: `${prefix}+c`,
    pasteAnnotation: `${prefix}+v`,
    close: 'escape',
    hideAllAnnotations: 'a',
    accept: 'enter',
    [ToolType.SelectTool]: 'v',
    [ToolType.SSIMTool]: 'd',
    [ToolType.RITMTool]: 'i',
    [ToolType.BoxTool]: 'b',
    [ToolType.CircleTool]: 'c',
    [ToolType.PolygonTool]: 'p',
    [ToolType.RotatedBoxTool]: 'r',
    [ToolType.GrabcutTool]: 'g',
    [ToolType.WatershedTool]: 'w',
    [ToolType.Explanation]: 'e',
    [ToolType.SegmentAnythingTool]: 'm',
    [ToolType.EditTool]: '/* not implemented */',
    [ToolType.KeypointTool]: '/* not implemented */',
});

export const defaultToolForProject = (domains: DOMAIN[]): ToolType => {
    if (domains.some(isSegmentationDomain)) {
        return ToolType.PolygonTool;
    }

    if (domains.some(isDetectionDomain)) {
        return ToolType.BoxTool;
    }

    if (domains.some(isRotatedDetectionDomain)) {
        return ToolType.RotatedBoxTool;
    }

    return ToolType.SelectTool;
};

export const getInitialAnnotations = (
    annotations = EMPTY_ANNOTATIONS,
    predictions = EMPTY_ANNOTATIONS,
    isTaskChainClassification = false
): ReadonlyArray<Annotation> => {
    if (isEmpty(predictions)) {
        return annotations;
    }

    // Fixes issue with missing predictions in the second task of a task chain
    if (isTaskChainClassification) {
        return annotations.map((annotation) => {
            const predictedAnnotation = predictions.find(hasEqualId(annotation.id));
            const noUserClassificationLabel = !annotation.labels.some(isGlobal);

            return predictedAnnotation && noUserClassificationLabel ? predictedAnnotation : annotation;
        });
    }

    // If we have predictions, and the annotations only include annotations without
    // labels (i.e. the global annotation added for classification projects) then
    // we return the predictions
    if (annotations.every(hasEmptyLabels)) {
        return predictions;
    }

    return annotations;
};
