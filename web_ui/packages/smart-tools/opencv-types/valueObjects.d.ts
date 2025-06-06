// Code generated using https://github.com/peteruhnak/opencv-ts
// License: Apache-2.0

declare module 'valueObjects' {
    import { int, float, double } from 'scalars';

    interface RangeLike {
        start: int;
        end: int;
    }

    class PathRange implements RangeLike {
        start: int;
        end: int;
        constructor(start?: int, end?: int);
    }

    interface TermCriteriaLike {
        type: int;
        maxCount: int;
        epsilon: double;
    }

    class TermCriteria implements TermCriteriaLike {
        type: int;
        maxCount: int;
        epsilon: double;
        constructor(type?: int, maxCount?: int, epsilon?: double);
    }

    interface SizeLike {
        width: number;
        height: number;
    }

    type Size2fLike = SizeLike;

    class Size implements SizeLike {
        width: number;
        height: number;
        constructor(width?: number, height?: number);
    }

    interface PointLike {
        readonly x: number;
        readonly y: number;
    }

    type Point2fLike = PointLike;

    class Point implements PointLike {
        readonly x: number;
        readonly y: number;
        constructor(x?: number, y?: number);
    }

    interface RectLike {
        readonly x: number;
        readonly y: number;
        readonly width: number;
        readonly height: number;
    }

    type Rect2fLike = RectLike;

    class Rect implements RectLike {
        readonly x: number;
        readonly y: number;
        readonly width: number;
        readonly height: number;
        constructor(x?: number, y?: number, width?: number, height?: number);
        constructor();
        constructor(point: PointLike, size: SizeLike);
        constructor(rect: RectLike);
    }

    interface RotatedRectLike {
        center: Point2fLike;
        size: Size2fLike;
        angle: float;
    }

    class RotatedRect implements RotatedRectLike {
        center: Point2fLike;
        size: Size2fLike;
        angle: float;
        constructor(center?: Point2fLike, size?: Size2fLike, angle?: float);
        static points(r: RotatedRectLike): PointLike[];
        static boundingRect2f(r: RotatedRectLike): PointLike;
    }

    function rotatedRectPoints(r: RotatedRectLike): [Point2fLike, Point2fLike, Point2fLike, Point2fLike];
    function rotatedRectBoundingRect(r: RotatedRectLike): RectLike;
    function rotatedRectBoundingRect2f(r: RotatedRectLike): Rect2fLike;

    interface KeyPointLike {
        angle: float;
        class_id: int;
        octave: int;
        pt: Point2fLike;
        response: float;
        size: int;
    }

    interface DMatchLike {
        queryIdx: int;
        trainIdx: int;
        imgIdx: int;
        distance: float;
    }

    class Scalar {
        [index: number]: double;
        constructor(v0?: double, v1?: double, v2?: double, v3?: double);
    }

    type ScalarLike = [double, double, double, double] | double[] | Scalar;

    interface MinMaxLocLike {
        minVal: double;
        maxVal: double;
        minLoc: PointLike;
        maxLoc: PointLike;
    }

    class MinMaxLoc implements MinMaxLocLike {
        minVal: double;
        maxVal: double;
        minLoc: PointLike;
        maxLoc: PointLike;
        constructor(minVal?: double, maxVal?: double, minLoc?: PointLike, maxLoc?: PointLike);
    }

    interface CircleLike {
        center: Point2fLike;
        radius: float;
    }

    class Circle implements CircleLike {
        center: Point2fLike;
        radius: float;
        constructor(center?: Point2fLike, radius?: float);
    }

    interface MomentsLike {
        m00: double;
        m10: double;
        m01: double;
        m20: double;
        m11: double;
        m02: double;
        m30: double;
        m21: double;
        m12: double;
        m03: double;
        mu20: double;
        mu11: double;
        mu02: double;
        mu30: double;
        mu21: double;
        mu12: double;
        mu03: double;
        nu20: double;
        nu11: double;
        nu02: double;
        nu30: double;
        nu21: double;
        nu12: double;
        nu03: double;
    }

    interface ExceptionLike {
        code: int;
        msg: string;
    }

    function exceptionFromPtr(ptr: number): ExceptionLike;
}
