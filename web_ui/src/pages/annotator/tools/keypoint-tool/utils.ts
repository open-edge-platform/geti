// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isEmpty from 'lodash/isEmpty';

import {
    AnnotationLabel,
    KeypointAnnotation,
    RegionOfInterest,
} from '../../../../core/annotations/annotation.interface';
import { degreesToRadians, getBoundingBox } from '../../../../core/annotations/math';
import { KeypointNode, Point } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { KeypointStructure } from '../../../../core/projects/task.interface';
import { isNonEmptyString } from '../../../../shared/utils';
import { KEYPOINT_RADIUS } from '../../../utils';
import { createAnnotation } from '../../utils';

export enum PointAxis {
    X = 'x',
    Y = 'y',
}

export enum CursorDirection {
    SouthEast = 'south-east',
    SouthWest = 'south-west',
    NorthEast = 'north-east',
    NorthWest = 'north-west',
}

export interface LabelPosition extends Partial<Point> {
    labelId: string;
}

export interface KeypointEdges {
    from: LabelPosition;
    to: LabelPosition;
}

export interface AnnotationInBoundingBox extends Point {
    label: AnnotationLabel;
    isVisible: boolean;
}

export interface PoseLocations {
    top: Point;
    bottom: Point;
    middle: Point;
    topWithGap: Point;
}

const cacheLabelPosition = (cache: { [key: string]: Point }, keypointNodes: KeypointNode[]) => (labelId: string) => {
    if (cache[labelId]) {
        return cache[labelId];
    }

    const matchedAnnotation = keypointNodes.find(({ label }) => label.id === labelId);

    if (matchedAnnotation) {
        cache[labelId] = { x: matchedAnnotation.x, y: matchedAnnotation.y };
    }

    return cache[labelId];
};

export const groupByFirstNode = (skeleton: KeypointStructure['edges']) => {
    return skeleton.reduce<Record<string, string[]>>((acc, { nodes }) => {
        const [firstNode, secondNode] = nodes;
        const isValidValue = isNonEmptyString(secondNode) && firstNode !== secondNode;

        if (isEmpty(firstNode)) {
            return acc;
        }

        if (!acc[firstNode]) {
            acc[firstNode] = [];
        }

        if (isValidValue && !acc[firstNode].includes(secondNode)) {
            acc[firstNode].push(secondNode);
        }
        return acc;
    }, {});
};

export const getPointsEdges = (keypointNodes: KeypointNode[], edges: KeypointStructure['edges']) => {
    const cache: { [key: string]: Point } = {};
    const getLabelPosition = cacheLabelPosition(cache, keypointNodes);
    const edgesGroupedByLabelName = groupByFirstNode(edges);

    return keypointNodes.flatMap((point) => {
        const groupedEdges = edgesGroupedByLabelName[point.label.id] ?? [];

        return groupedEdges.map((edgeEnding) => ({
            from: { labelId: point.label.id, x: point.x, y: point.y },
            to: { labelId: edgeEnding, ...getLabelPosition(edgeEnding) },
        }));
    });
};

export const getPercentageFromPoint = (point: Point, roi: RegionOfInterest) => {
    return {
        x: ((point.x - roi.x) / roi.width) * 100,
        y: ((point.y - roi.y) / roi.height) * 100,
    };
};

export const getPointFromPercentage = (point: Point, roi: RegionOfInterest) => {
    return {
        x: (point.x / 100) * roi.width,
        y: (point.y / 100) * roi.height,
    };
};

export const MIN_BOUNDING_BOX_SIZE = 10;
export const PADDING_MULTIPLIER = KEYPOINT_RADIUS * 4;

export const getMinBoundingBox = (boundingBox: RegionOfInterest): RegionOfInterest => {
    return {
        ...boundingBox,
        width: boundingBox.width <= MIN_BOUNDING_BOX_SIZE ? MIN_BOUNDING_BOX_SIZE : boundingBox.width,
        height: boundingBox.height <= MIN_BOUNDING_BOX_SIZE ? MIN_BOUNDING_BOX_SIZE : boundingBox.height,
    };
};

const getPaddedBoundingBox = (symbol: 1 | -1) => (boundingBox: RegionOfInterest, zoom: number) => {
    const smallestSide = Math.min(boundingBox.width, boundingBox.height);
    const padding = Math.min(smallestSide * 0.1, PADDING_MULTIPLIER / zoom);

    return {
        x: boundingBox.x + symbol * padding,
        y: boundingBox.y + symbol * padding,
        width: boundingBox.width - symbol * padding * 2,
        height: boundingBox.height - symbol * padding * 2,
    };
};

export const getOuterPaddedBoundingBox = getPaddedBoundingBox(-1);
export const getInnerPaddedBoundingBox = getPaddedBoundingBox(1);

export const getAnnotationInBoundingBox = (points: KeypointNode[], boundingBox: RegionOfInterest) => {
    const skeletonBoundingBox = getBoundingBox({ shapeType: ShapeType.Pose, points });

    const newPoints = points.map((point: KeypointNode) => {
        const percentagePoint = getPercentageFromPoint(point, skeletonBoundingBox);
        const coordinates = getPointFromPercentage(percentagePoint, boundingBox);
        const offset = { x: boundingBox.x, y: boundingBox.y };

        const x = Math.round(coordinates.x + offset.x);
        const y = Math.round(coordinates.y + offset.y);

        return { ...point, x, y };
    });

    return createAnnotation({ shapeType: ShapeType.Pose, points: newPoints }, []) as KeypointAnnotation;
};

export const mirrorPointsAcrossAxis = <T extends Point>(points: T[], pointAxis: PointAxis): T[] => {
    const minAxisValue = Math.min(...points.map((point) => point[pointAxis]));
    const maxAxisValue = Math.max(...points.map((point) => point[pointAxis]));
    const axisCenter = (minAxisValue + maxAxisValue) / 2;

    return points.map((point) => ({
        ...point,
        [pointAxis]: axisCenter - (point[pointAxis] - axisCenter),
    }));
};

export const getDirection = (startPoint: Point, endPoint: Point): CursorDirection => {
    if (endPoint.x >= startPoint.x && endPoint.y >= startPoint.y) {
        return CursorDirection.SouthEast;
    }

    if (endPoint.x <= startPoint.x && endPoint.y >= startPoint.y) {
        return CursorDirection.SouthWest;
    }

    if (endPoint.x >= startPoint.x && endPoint.y <= startPoint.y) {
        return CursorDirection.NorthEast;
    }
    return CursorDirection.NorthWest;
};

export const getTemplateWithDirection = (templatePoints: KeypointNode[], cursorDirection: CursorDirection) => {
    if (cursorDirection === CursorDirection.SouthWest) {
        return mirrorPointsAcrossAxis(templatePoints, PointAxis.X);
    }
    if (cursorDirection === CursorDirection.NorthEast) {
        return mirrorPointsAcrossAxis(templatePoints, PointAxis.Y);
    }
    if (cursorDirection === CursorDirection.NorthWest) {
        return mirrorPointsAcrossAxis(mirrorPointsAcrossAxis(templatePoints, PointAxis.Y), PointAxis.X);
    }
    return templatePoints;
};

const getMaxMinPoint = <T extends Point>(points: T[], pointAxis: PointAxis) => {
    const minAxisValue = Math.min(...points.map((point) => point[pointAxis]));
    const maxAxisValue = Math.max(...points.map((point) => point[pointAxis]));
    return [minAxisValue, maxAxisValue];
};

export const getPoseLocations = (points: KeypointNode[], gap: number): PoseLocations => {
    const [minX, maxX] = getMaxMinPoint(points, PointAxis.X);
    const [minY, maxY] = getMaxMinPoint(points, PointAxis.Y);

    const top = { x: minX, y: minY };
    const bottom = { x: maxX, y: maxY };
    const middle = { x: (top.x + bottom.x) / 2, y: (top.y + bottom.y) / 2 };

    return {
        top,
        bottom,
        middle,
        topWithGap: { ...top, y: top.y - gap * 2 },
    };
};

export const rotatePointsAroundPivot = <T extends Point>(points: T[], pivot: Point, angleDegrees: number) => {
    const angleRadians = degreesToRadians(angleDegrees);

    return points.map(({ x, y, ...others }) => {
        const deltaX = x - pivot.x;
        const deltaY = y - pivot.y;

        const rotatedX = Math.cos(angleRadians) * deltaX - Math.sin(angleRadians) * deltaY + pivot.x;
        const rotatedY = Math.sin(angleRadians) * deltaX + Math.cos(angleRadians) * deltaY + pivot.y;

        return { ...others, x: Math.round(rotatedX), y: Math.round(rotatedY) };
    });
};
