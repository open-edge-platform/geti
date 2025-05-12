// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { PointerEvent, SVGProps } from 'react';

import defer from 'lodash/defer';

import { Annotation } from '../../../core/annotations/annotation.interface';
import { Point } from '../../../core/annotations/shapes.interface';
import { isPolygon, isPoseShape } from '../../../core/annotations/utils';
import { Label } from '../../../core/labels/label.interface';
import { isLeftButton, isWheelButton } from '../../buttons-utils';
import { ToolLabel, ToolType } from '../core/annotation-tool-context.interface';
import { PolygonMode } from './polygon-tool/polygon-tool.enum';

export const DEFAULT_ANNOTATION_STYLES = {
    fillOpacity: 'var(--annotation-fill-opacity)',
    fill: 'var(--energy-blue)',
    stroke: 'var(--energy-blue)',
};

export const EDIT_ANNOTATION_STYLES = {
    stroke: 'var(--energy-blue-light)',
};

export const EDIT_SIZE_ANNOTATION_STYLES = {
    fillOpacity: 'var(--annotation-fill-opacity)',
    fill: 'var(--energy-blue-light)',
    stroke: 'var(--energy-blue-light)',
};

export const SELECT_ANNOTATION_STYLES = {
    fillOpacity: 0.3,
    fill: 'var(--energy-blue-shade)',
    stroke: 'var(--energy-blue-shade)',
    strokeWidth: 'calc(2px / var(--zoom-level))',
};

export const GRABCUT_RESULT_BOX_STYLES = {
    fillOpacity: 0,
    stroke: 'var(--energy-blue-shade)',
    strokeWidth: 'calc(2px / var(--zoom-level))',
    strokeDasharray: 'calc(10 / var(--zoom-level))',
};

export const drawingStyles = (defaultLabel: Label | null): typeof DEFAULT_ANNOTATION_STYLES => {
    if (defaultLabel === null) {
        return DEFAULT_ANNOTATION_STYLES;
    }

    return {
        ...DEFAULT_ANNOTATION_STYLES,
        fill: defaultLabel.color,
        stroke: defaultLabel.color,
    };
};

type OnPointerDown = SVGProps<SVGElement>['onPointerDown'];
export const allowPanning = (onPointerDown?: OnPointerDown): OnPointerDown | undefined => {
    if (onPointerDown === undefined) {
        return;
    }

    return (event: PointerEvent<SVGElement>) => {
        const isPressingPanningHotKeys = (isLeftButton(event) && event.ctrlKey) || isWheelButton(event);

        if (isPressingPanningHotKeys) {
            return;
        }

        return onPointerDown(event);
    };
};

export const blurActiveInput = (isFocused: boolean): void => {
    const element = document.activeElement;

    if (isFocused && element?.nodeName === 'INPUT') {
        defer(() => (element as HTMLInputElement).blur());
    }
};

export const translateAnnotation = (annotation: Annotation, translateVector: Point): Annotation => {
    const { shape } = annotation;

    if (isPolygon(shape)) {
        return {
            ...annotation,
            shape: {
                ...shape,
                points: shape.points.map(({ x, y }) => ({
                    x: x + translateVector.x,
                    y: y + translateVector.y,
                })),
            },
        };
    }

    if (isPoseShape(shape)) {
        return {
            ...annotation,
            shape: {
                ...shape,
                points: shape.points.map(({ x, y, ...others }) => ({
                    ...others,
                    x: x + translateVector.x,
                    y: y + translateVector.y,
                })),
            },
        };
    }

    return {
        ...annotation,
        shape: {
            ...shape,
            x: shape.x + translateVector.x,
            y: shape.y + translateVector.y,
        },
    };
};

export type ExtendedToolType = ToolType | PolygonMode.MagneticLasso | PolygonMode.Lasso;

export const toolTypeToLabelMapping: Record<ExtendedToolType, string> = {
    [ToolType.BoxTool]: ToolLabel.BoxTool,
    [ToolType.CircleTool]: ToolLabel.CircleTool,
    [ToolType.PolygonTool]: ToolLabel.PolygonTool,
    [ToolType.GrabcutTool]: ToolLabel.GrabcutTool,
    [ToolType.WatershedTool]: ToolLabel.WatershedTool,
    [ToolType.SSIMTool]: ToolLabel.SSIMTool,
    [ToolType.RotatedBoxTool]: ToolLabel.RotatedBoxTool,
    [ToolType.RITMTool]: ToolLabel.RITMTool,
    [ToolType.SegmentAnythingTool]: ToolLabel.SegmentAnythingTool,
    [ToolType.SelectTool]: ToolLabel.SelectTool,
    [ToolType.EditTool]: ToolLabel.EditTool,
    [ToolType.Explanation]: ToolLabel.Explanation,
    [PolygonMode.MagneticLasso]: `${ToolLabel.PolygonTool} - snapping mode`,
    [PolygonMode.Lasso]: `${ToolLabel.PolygonTool} - freehand selection mode`,
    [ToolType.KeypointTool]: ToolLabel.KeypointTool,
};

export const toolLabelToTypeMapping: Record<ToolLabel, ToolType> = {
    [ToolLabel.BoxTool]: ToolType.BoxTool,
    [ToolLabel.CircleTool]: ToolType.CircleTool,
    [ToolLabel.PolygonTool]: ToolType.PolygonTool,
    [ToolLabel.GrabcutTool]: ToolType.GrabcutTool,
    [ToolLabel.WatershedTool]: ToolType.WatershedTool,
    [ToolLabel.SSIMTool]: ToolType.SSIMTool,
    [ToolLabel.RotatedBoxTool]: ToolType.RotatedBoxTool,
    [ToolLabel.RITMTool]: ToolType.RITMTool,
    [ToolLabel.SegmentAnythingTool]: ToolType.SegmentAnythingTool,
    [ToolLabel.SelectTool]: ToolType.SelectTool,
    [ToolLabel.EditTool]: ToolType.EditTool,
    [ToolLabel.Explanation]: ToolType.Explanation,
    [ToolLabel.KeypointTool]: ToolType.KeypointTool,
};

export const SENSITIVITY_SLIDER_TOOLTIP =
    'Adjust the precision level by selecting a number from the drop-down menu: higher numbers increase precision, ' +
    'while lower numbers decrease it. Keep in mind that increased precision requires more computing power and time. ' +
    'Adding high-resolution images may further extend the annotation waiting time significantly.';
