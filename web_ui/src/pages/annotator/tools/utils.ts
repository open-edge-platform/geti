// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { PointerEvent, SVGProps } from 'react';

import { area, booleanIntersects, difference, featureCollection, polygon, union } from '@turf/turf';
import { Feature, GeoJsonProperties, Polygon as GeoPolygon, MultiPolygon, Position } from 'geojson';
import defer from 'lodash/defer';

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

type TurfPolygon = Feature<GeoPolygon, GeoJsonProperties>;

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

const calculateRectanglePoints = (shape: BoundingBox): Position[] => {
    const { x: X, y: Y, width, height } = shape;
    const topLeftPoint = [X, Y];
    const topRightPoint = [X + width, Y];
    const bottomLeftPoint = [X, Y + height];
    const bottomRightPoint = [X + width, Y + height];

    return [topLeftPoint, topRightPoint, bottomRightPoint, bottomLeftPoint];
};

const calculateRotatedRectanglePoints = (shape: RotatedRect): Position[] => {
    return rotatedRectCorners(shape).map(Vec2.toTurfPoint);
};

const calculateCirclePoints = (shape: Circle): Position[] => {
    const stepAngle = 5;
    const endAngle = 360;
    const { x: centerX, y: centerY, r } = shape;

    let points: Position[] = [];

    for (let i = 0; i <= endAngle; i += stepAngle) {
        const X = centerX + r * Math.cos((i * Math.PI) / 180);
        const Y = centerY + r * Math.sin((i * Math.PI) / 180);

        points = [...points, [X, Y]];
    }

    return points;
};

const convertPolygonPoints = (shape: Polygon): Position[] => {
    return shape.points.map(({ x, y }: Point) => [x, y]);
};

export const shapeToTurfPolygon = (shape: Shape): TurfPolygon => {
    switch (true) {
        case isRect(shape): {
            const points = calculateRectanglePoints(shape);
            // Ensure the polygon is closed by adding the first point at the end
            return polygon([[...points, points[0]]]);
        }
        case isRotatedRect(shape): {
            const points = calculateRotatedRectanglePoints(shape);
            // Ensure the polygon is closed by adding the first point at the end
            return polygon([[...points, points[0]]]);
        }
        case isCircle(shape): {
            const points = calculateCirclePoints(shape);
            // Ensure the polygon is closed by adding the first point at the end
            return polygon([[...points, points[0]]]);
        }
        case isPoseShape(shape): {
            const points = calculateRectanglePoints(getBoundingBox(shape));
            // Ensure the polygon is closed by adding the first point at the end
            return polygon([[...points, points[0]]]);
        }
        default: {
            // Polygon
            const points = convertPolygonPoints(shape);
            // For polygons, ensure it's closed by comparing first and last points
            const isAlreadyClosed =
                points.length > 0 &&
                points[0][0] === points[points.length - 1][0] &&
                points[0][1] === points[points.length - 1][1];

            // If not closed, add the first point to the end
            return polygon([isAlreadyClosed ? points : [...points, points[0]]]);
        }
    }
};

export const isPolygonValid = (pol: Polygon | null): boolean => {
    if (!pol) return false;

    // Check if polygon has enough points first
    if (pol.points.length < 3) {
        return false;
    }

    try {
        const turfPolygon = shapeToTurfPolygon(pol);

        return Math.abs(area(turfPolygon)) > POLYGON_VALID_AREA;
    } catch (error) {
        console.error('Error validating polygon:', error);
        return false;
    }
};
const turfToPolygon = (turfPolygon: TurfPolygon): Polygon => {
    const coordinates = turfPolygon.geometry.coordinates[0];
    // Remove the last point which is a duplicate of the first (to close the polygon)
    const points = coordinates.slice(0, -1).map(([x, y]: number[]) => ({ x, y }));

    return {
        shapeType: ShapeType.Polygon,
        points,
    };
};

const findLargestPolygon = (multiPolygon: Feature<GeoPolygon | MultiPolygon>): Feature<GeoPolygon> => {
    if (!multiPolygon || !multiPolygon.geometry) {
        return polygon([[]]);
    }

    // If it's a simple polygon, return it
    if (multiPolygon.geometry.type === 'Polygon') {
        return multiPolygon as Feature<GeoPolygon>;
    }

    // If it's a multipolygon, find the largest one
    if (multiPolygon.geometry.type === 'MultiPolygon') {
        let maxArea = 0;
        let largestPoly = multiPolygon.geometry.coordinates[0];

        multiPolygon.geometry.coordinates.forEach((polyCoords: Position[][]) => {
            const poly = polygon(polyCoords);
            const polyArea = area(poly);

            if (polyArea > maxArea) {
                maxArea = polyArea;
                largestPoly = polyCoords;
            }
        });

        return polygon(largestPoly);
    }

    return polygon([[]]);
};

const filterIntersectedPolygonsWithRoi = (
    roi: RegionOfInterest,
    turfPolygon: Feature<GeoPolygon | MultiPolygon>
): Feature<GeoPolygon> => {
    const roiPoly = shapeToTurfPolygon({ ...roi, shapeType: ShapeType.Rect });

    // If this is a multipolygon, filter out parts that don't intersect with ROI
    if (turfPolygon.geometry.type === 'MultiPolygon') {
        const intersectingPolys = turfPolygon.geometry.coordinates
            .filter((polyCoords: Position[][]) => {
                const poly = polygon(polyCoords);
                return booleanIntersects(poly, roiPoly);
            })
            .map((polyCoords: Position[][]) => polygon(polyCoords));

        if (intersectingPolys.length === 0) {
            return polygon([[]]);
        }

        if (intersectingPolys.length === 1) {
            return intersectingPolys[0];
        }

        // Find the largest among intersecting polygons
        return intersectingPolys.reduce((largest, current) => {
            return area(current) > area(largest) ? current : largest;
        }, intersectingPolys[0]);
    }

    return booleanIntersects(turfPolygon, roiPoly) ? (turfPolygon as Feature<GeoPolygon>) : polygon([[]]);
};

export const getShapesUnion = (roi: RegionOfInterest, subj: Shape, clip: Shape): Polygon => {
    const subjPoly = shapeToTurfPolygon(subj);
    const clipPoly = shapeToTurfPolygon(clip);

    try {
        const result = union(featureCollection([subjPoly, clipPoly]));
        const filtered = result ? filterIntersectedPolygonsWithRoi(roi, result) : polygon([[]]);
        const largest = findLargestPolygon(filtered);

        return turfToPolygon(largest);
    } catch (error) {
        console.error('Error in getShapesUnion:', error);
        return turfToPolygon(subjPoly); // Fallback to original shape
    }
};

export const getShapesDifference = (roi: RegionOfInterest, subj: Shape, clip: Shape): Polygon => {
    const subjPoly = shapeToTurfPolygon(subj);
    const clipPoly = shapeToTurfPolygon(clip);

    try {
        const result = difference(featureCollection([subjPoly, clipPoly]));
        const filtered = result ? filterIntersectedPolygonsWithRoi(roi, result) : polygon([[]]);
        const largest = findLargestPolygon(filtered);

        return turfToPolygon(largest);
    } catch (error) {
        console.error('Error in getShapesDifference:', error);
        return turfToPolygon(subjPoly); // Fallback to original shape
    }
};

export const isShapeWithinRoi = (roi: RegionOfInterest, shape: Shape): boolean => {
    if (isRect(shape)) {
        return isRectWithinRoi(roi, shape);
    }

    if (isCircle(shape)) {
        const { r, x, y } = shape;
        const isCirclePartiallyWithinRoi =
            x + r >= roi.x && x - r <= roi.x + roi.width && y + r >= roi.y && y - r <= roi.y + roi.height;

        return isCirclePartiallyWithinRoi;
    }

    const shapePoly = shapeToTurfPolygon(shape);
    const roiPoly = shapeToTurfPolygon({ ...roi, shapeType: ShapeType.Rect });

    return booleanIntersects(roiPoly, shapePoly);
};

export const isShapePartiallyWithinROI = (roi: RegionOfInterest, shape: Shape): boolean => {
    if (isRect(shape)) {
        const rect = shape as Rect;
        // If any of these conditions is true, the rectangles don't intersect
        if (
            rect.x + rect.width <= roi.x || // Rectangle is completely to the left of ROI
            rect.x >= roi.x + roi.width || // Rectangle is completely to the right of ROI
            rect.y + rect.height <= roi.y || // Rectangle is completely above ROI
            rect.y >= roi.y + roi.height
        ) {
            // Rectangle is completely below ROI
            return false;
        }
        return true;
    }

    const shapePoly = shapeToTurfPolygon(shape);
    const roiPoly = shapeToTurfPolygon({ ...roi, shapeType: ShapeType.Rect });

    return booleanIntersects(roiPoly, shapePoly);
};

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
