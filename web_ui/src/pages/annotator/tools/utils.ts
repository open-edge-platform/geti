// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { PointerEvent, SVGProps } from 'react';

import Clipper from '@doodle3d/clipper-js';
import type ClipperShape from '@doodle3d/clipper-js';
import { defer, isEmpty } from 'lodash-es';

import { Annotation, RegionOfInterest } from '../../../core/annotations/annotation.interface';
import { BoundingBox, getBoundingBox, getCenterOfShape, rotatedRectCorners } from '../../../core/annotations/math';
import { Circle, Point, Polygon, Rect, RotatedRect, Shape } from '../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../core/annotations/shapetype.enum';
import { isCircle, isPolygon, isPoseShape, isRect, isRotatedRect } from '../../../core/annotations/utils';
import * as Vec2 from '../../../core/annotations/vec2';
import { Label } from '../../../core/labels/label.interface';
import { isLeftButton, isWheelButton } from '../../buttons-utils';
import { ToolLabel, ToolType } from '../core/annotation-tool-context.interface';
import { PolygonMode } from './polygon-tool/polygon-tool.enum';

// TODO: this will be removed when https://github.com/open-edge-platform/geti/pull/185 is merged
// @ts-expect-error `default` actually exists in the module
const ClipperJS = Clipper.default || Clipper;

export interface ClipperPoint {
    X: number;
    Y: number;
}

const POLYGON_VALID_AREA = 4;

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

const calculateRectanglePoints = (shape: BoundingBox): ClipperPoint[] => {
    const { x: X, y: Y, width, height } = shape;
    const topLeftPoint = { X, Y };
    const topRightPoint = { X: X + width, Y };
    const bottomLeftPoint = { X, Y: Y + height };
    const bottomRightPoint = { X: X + width, Y: Y + height };

    return [topLeftPoint, topRightPoint, bottomRightPoint, bottomLeftPoint];
};

const calculateRotatedRectanglePoints = (shape: RotatedRect): ClipperPoint[] => {
    return rotatedRectCorners(shape).map(Vec2.toClipperPoint);
};

const calculateCirclePoints = (shape: Circle): ClipperPoint[] => {
    const stepAngle = 5;
    const endAngle = 360;
    const { x: centerX, y: centerY, r } = shape;

    let points: ClipperPoint[] = [];

    for (let i = 0; i <= endAngle; i += stepAngle) {
        const X = centerX + r * Math.cos((i * Math.PI) / 180);
        const Y = centerY + r * Math.sin((i * Math.PI) / 180);

        points = [...points, { X, Y }];
    }

    return points;
};

const convertPolygonPoints = (shape: Polygon): ClipperPoint[] => {
    return shape.points.map(({ x, y }: Point) => ({ X: x, Y: y }));
};

export const transformToClipperShape = (shape: Shape): ClipperShape => {
    switch (true) {
        case isRect(shape):
            return new ClipperJS([calculateRectanglePoints(shape)], true);
        case isRotatedRect(shape):
            return new ClipperJS([calculateRotatedRectanglePoints(shape)], true);
        case isCircle(shape):
            return new ClipperJS([calculateCirclePoints(shape)], true);
        case isPoseShape(shape):
            return new ClipperJS([calculateRectanglePoints(getBoundingBox(shape))], true);
        default:
            return new ClipperJS([convertPolygonPoints(shape)], true);
    }
};

export const isPolygonValid = (polygon: Polygon | null): boolean => {
    if (!polygon) return false;

    const sPolygon = transformToClipperShape(polygon);

    return Math.abs(sPolygon.totalArea()) > POLYGON_VALID_AREA;
};

const clipperShapeToPolygon = (path: ClipperPoint[]): Polygon => ({
    shapeType: ShapeType.Polygon,
    points: path.map(({ X, Y }) => ({ x: X, y: Y })),
});

const filterIntersectedPathsWithRoi = (roi: RegionOfInterest, shape: ClipperShape): ClipperShape => {
    const newPath = shape.clone();
    const roiRect = transformToClipperShape({ ...roi, shapeType: ShapeType.Rect });

    newPath.paths = newPath.paths.filter((subPath) => hasIntersection(roiRect, new ClipperJS([subPath])));

    return newPath;
};

const findBiggerSubPath = (shape: ClipperShape): ClipperPoint[] => {
    const areas = shape.areas();
    const { index: shapeIndex } = areas.reduce(
        (accum: { value: number; index: number }, value, index) => {
            return value > accum.value ? { value, index } : accum;
        },
        { value: 0, index: 0 }
    );

    return shape.paths.length ? shape.paths[shapeIndex] : [];
};

const runUnionOrDifference =
    <T>(algorithm: 'union' | 'difference', formatTo: (path: ClipperPoint[]) => T) =>
    (roi: RegionOfInterest, subj: Shape, clip: Shape): T => {
        const subjShape = transformToClipperShape(subj);
        const clipShape = transformToClipperShape(clip);
        const solutionPath = subjShape[algorithm](clipShape);
        const filteredPath = filterIntersectedPathsWithRoi(roi, solutionPath);
        const biggestPath = findBiggerSubPath(filteredPath);

        return formatTo(biggestPath);
    };

export const getShapesUnion = runUnionOrDifference<Polygon>('union', clipperShapeToPolygon);

export const getShapesDifference = runUnionOrDifference<Polygon>('difference', clipperShapeToPolygon);

const removeOffPointsRect = (rect: Rect, roi: RegionOfInterest): Rect => {
    const { x, y, width, height } = roi;

    let newRect: Rect = {
        ...rect,
    };

    if (rect.x < x) {
        newRect = {
            ...newRect,
            x,
            width: newRect.width - (x - rect.x),
        };
    }

    if (rect.x + rect.width > x + width) {
        const diff = rect.x + rect.width - x - width;

        newRect = {
            ...newRect,
            width: rect.width - diff,
        };
    }

    if (rect.y < y) {
        newRect = {
            ...newRect,
            y,
            height: rect.height - (y - rect.y),
        };
    }

    if (newRect.y + rect.height > y + height) {
        const diff = rect.y + rect.height - y - height;

        newRect = {
            ...newRect,
            height: rect.height - diff,
        };
    }

    return newRect;
};

export const removeOffLimitPointsPolygon = (shape: Shape, roi: RegionOfInterest): Polygon => {
    const { width, height, x, y } = roi;
    const getRect = (rx: number, ry: number, rWidth: number, rHeight: number): Rect => ({
        x: rx,
        y: ry,
        width: rWidth,
        height: rHeight,
        shapeType: ShapeType.Rect,
    });
    // `eraserSize` Builds and positions rect shapes around ROI limits (top, left, right, bottom),
    // finally `getShapesDifference` will use those rects to calc and remove offline polygons
    const eraserSize = 10;
    const topRect = getRect(x - eraserSize, y - eraserSize, width + eraserSize * 3, eraserSize);
    const leftRect = getRect(x - eraserSize, y - eraserSize, eraserSize, height * 2);
    const rightRect = getRect(x + width, y - eraserSize, eraserSize, height * 2);
    const bottomRect = getRect(x - eraserSize, y + height, width + eraserSize * 3, eraserSize);

    return [leftRect, bottomRect, rightRect, topRect].reduce(
        (accum, current) => getShapesDifference(roi, accum, current),
        shape
    ) as Polygon;
};

export const removeOffLimitPoints = (shape: Shape, roi: RegionOfInterest): Shape => {
    if (isRotatedRect(shape)) {
        return shape;
    }

    if (isCircle(shape)) {
        return shape;
    }

    if (isPoseShape(shape)) {
        return shape;
    }

    return isRect(shape) ? removeOffPointsRect(shape, roi) : removeOffLimitPointsPolygon(shape, roi);
};

const hasIntersection = (clip: ClipperShape, subj: ClipperShape) => {
    const { paths } = clip.intersect(subj);

    return !isEmpty(paths);
};

export const isPointWithinRoi = (roi: RegionOfInterest, point: Point): boolean => {
    const isValidX = point.x >= roi.x && point.x <= roi.x + roi.width;
    const isValidY = point.y >= roi.y && point.y <= roi.y + roi.height;

    return isValidX && isValidY;
};

export const isRectWithinRoi = (roi: RegionOfInterest, rect: Omit<Rect, 'shapeType'>): boolean => {
    const isValidPosition = isPointWithinRoi(roi, rect);
    const isValidWidth = isPointWithinRoi(roi, { x: rect.x + rect.width, y: rect.y });
    const isValidHeight = isPointWithinRoi(roi, { x: rect.x, y: rect.y + rect.height });

    return isValidPosition && isValidWidth && isValidHeight;
};

export const isShapePartiallyWithinROI = (roi: RegionOfInterest, shape: Shape): boolean => {
    const clipperShape = transformToClipperShape(shape);
    const roiShape = transformToClipperShape({ ...roi, shapeType: ShapeType.Rect });

    return hasIntersection(roiShape, clipperShape);
};

export const isShapeWithinRoi = (roi: RegionOfInterest, shape: Shape): boolean => {
    if (isRect(shape)) {
        return isRectWithinRoi(roi, shape);
    }

    // hasIntersection returns false for circle with radius < 3
    if (isCircle(shape) && shape.r < 3) {
        const { r, x, y } = shape;
        const isCirclePartiallyWithinRoi =
            x + r >= roi.x || x + r <= roi.width || y + r >= roi.y || y + r <= roi.height;

        return isCirclePartiallyWithinRoi;
    }

    const clipperShape = transformToClipperShape(shape);
    const roiShape = transformToClipperShape({ ...roi, shapeType: ShapeType.Rect });

    return hasIntersection(roiShape, clipperShape);
};

export const isInsideBoundingBox =
    <T extends { shape: Shape }>(element: T) =>
    (boundingBox: RegionOfInterest): boolean => {
        if (isCircle(element.shape)) {
            return isShapeWithinRoi(boundingBox, element.shape);
        }

        return isPointWithinRoi(boundingBox, getCenterOfShape(element.shape));
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
