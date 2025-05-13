// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    area,
    booleanContains,
    booleanIntersects,
    booleanPointInPolygon,
    center,
    centroid,
    difference,
    featureCollection,
    point,
    polygon,
    union,
} from '@turf/turf';
import { Feature, Polygon as GeoPolygon, MultiPolygon, Position } from 'geojson';

import { RegionOfInterest } from '../../../core/annotations/annotation.interface';
import { BoundingBox, getBoundingBox, rotatedRectCorners } from '../../../core/annotations/math';
import { Circle, Point, Polygon, Rect, RotatedRect, Shape } from '../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../core/annotations/shapetype.enum';
import { isCircle, isPoseShape, isRect, isRotatedRect } from '../../../core/annotations/utils';
import { Vec2 } from '../../../core/annotations/vec2';

export type TurfPolygon = Feature<GeoPolygon>;

const POLYGON_VALID_AREA = 4;

const convertPolygonToTurf = (shape: Polygon): Position[] => {
    return shape.points.map(toTurfPoint);
};

export const toTurfPoint = ({ x, y }: Vec2): number[] => {
    return [x, y];
};

const convertTurfToPolygon = (turfPolygon: TurfPolygon): Polygon => {
    const coordinates = turfPolygon.geometry.coordinates[0];

    // Remove the last point which is a duplicate of the first (to close the polygon)
    const points = coordinates.slice(0, -1).map(([x, y]: number[]) => ({ x, y }));

    return {
        shapeType: ShapeType.Polygon,
        points,
    };
};

export const calculateRectanglePoints = (shape: BoundingBox): Position[] => {
    const { x: X, y: Y, width, height } = shape;
    const topLeftPoint = [X, Y];
    const topRightPoint = [X + width, Y];
    const bottomLeftPoint = [X, Y + height];
    const bottomRightPoint = [X + width, Y + height];

    return [topLeftPoint, topRightPoint, bottomRightPoint, bottomLeftPoint];
};

export const calculateRotatedRectanglePoints = (shape: RotatedRect): Position[] => {
    return rotatedRectCorners(shape).map(toTurfPoint);
};

export const calculateCirclePoints = (shape: Circle): Position[] => {
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
            const points = convertPolygonToTurf(shape);

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

export const calculatePolygonArea = (turfPolygon: TurfPolygon): number => {
    let totalArea = 0;
    const points = turfPolygon.geometry.coordinates[0];

    for (let i = 0; i < points.length; i++) {
        const [x1, y1] = points[i];
        const [x2, y2] = points[(i + 1) % points.length];

        totalArea += x1 * y2;
        totalArea -= y1 * x2;
    }

    return Math.abs(totalArea) / 2;
};

export const isPolygonValid = (pol: Polygon | null): boolean => {
    if (!pol) return false;

    // Check if polygon has enough points first
    if (pol.points.length < 3) {
        return false;
    }

    const turfPolygon = shapeToTurfPolygon(pol);

    const polygonArea = calculatePolygonArea(turfPolygon);
    if (polygonArea < POLYGON_VALID_AREA) {
        return false;
    }

    return true;
};

export const findLargestPolygon = (multiPolygon: Feature<GeoPolygon | MultiPolygon>): Feature<GeoPolygon> => {
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

export const getShapesUnion = (roi: RegionOfInterest, main: Shape, sub: Shape): Polygon => {
    const mainPolygon = shapeToTurfPolygon(main);
    const subPolygon = shapeToTurfPolygon(sub);

    const result = union(featureCollection([mainPolygon, subPolygon]));
    const filtered = result ? filterIntersectedPolygonsWithRoi(roi, result) : polygon([[]]);
    const largest = findLargestPolygon(filtered);

    return convertTurfToPolygon(largest);
};

export const getShapesDifference = (roi: RegionOfInterest, main: Shape, sub: Shape): Polygon => {
    const mainPolygon = shapeToTurfPolygon(main);
    const subPolygon = shapeToTurfPolygon(sub);

    const result = difference(featureCollection([mainPolygon, subPolygon]));
    const filtered = result ? filterIntersectedPolygonsWithRoi(roi, result) : polygon([[]]);
    const largest = findLargestPolygon(filtered);

    return convertTurfToPolygon(largest);
};

export const isShapeWithinRoi = (roi: RegionOfInterest, shape: Shape): boolean => {
    const shapePoly = shapeToTurfPolygon(shape);
    const roiPoly = shapeToTurfPolygon({ ...roi, shapeType: ShapeType.Rect });

    return booleanContains(roiPoly, shapePoly);
};

export const isShapePartiallyWithinROI = (roi: RegionOfInterest, shape: Shape): boolean => {
    const shapePoly = shapeToTurfPolygon(shape);
    const roiPoly = shapeToTurfPolygon({ ...roi, shapeType: ShapeType.Rect });

    return !booleanContains(roiPoly, shapePoly) && booleanIntersects(roiPoly, shapePoly);
};

export const isCenterOfShapeWithinROI = (roi: RegionOfInterest, shape: Shape) => {
    const shapePoly = shapeToTurfPolygon(shape);
    const roiPoly = shapeToTurfPolygon({ ...roi, shapeType: ShapeType.Rect });

    const shapeCentroid = centroid(shapePoly);

    return booleanPointInPolygon(shapeCentroid, roiPoly);
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

export const isPointWithinRoi = (roi: RegionOfInterest, _point: Point): boolean => {
    const turfPoint = point([_point.x, _point.y]);
    const roiPoly = shapeToTurfPolygon({ ...roi, shapeType: ShapeType.Rect });

    return booleanPointInPolygon(turfPoint, roiPoly);
};

export const getCenterOfShape = (shape: Shape): Point => {
    const shapePolygon = shapeToTurfPolygon(shape);
    const shapeCentroid = centroid(shapePolygon);

    return { x: shapeCentroid.geometry.coordinates[0], y: shapeCentroid.geometry.coordinates[1] };
};

export const getCenterOfMultipleAnnotations = (shapes: Shape[]): Point => {
    const shapePolygons = shapes.map(shapeToTurfPolygon);
    const centerFeature = center(featureCollection(shapePolygons));
    const [x, y] = centerFeature.geometry.coordinates;

    return { x, y };
};

export const isInsideBoundingBox =
    <T extends { shape: Shape }>(element: T) =>
    (boundingBox: RegionOfInterest): boolean => {
        if (isCircle(element.shape)) {
            return isShapeWithinRoi(boundingBox, element.shape);
        }

        return isPointWithinRoi(boundingBox, getCenterOfShape(element.shape));
    };
