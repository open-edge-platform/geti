// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

enum LABEL_BEHAVIOUR {
    // A local label is applied to a shape to localize a point of interest. It is
    // used by the detection and segmentation tasks.
    // Only 1 localized label can be applied to an annotation at a time.
    // An exception exists for anomaly detection and anomaly segmentation, whose
    // "anomalous" label is both LOCAL and GLOBAL.
    LOCAL = 1 << 1,

    // A global label classifies an ROI. An annotation can have more than 1
    // global label.
    // It is used by classification and anomaly classification tasks as well as
    // any exclusive label.
    GLOBAL = 1 << 2,

    // When applying an exclusive label to a media item or to an annotation (in case
    // of a task chain project) we will remove all annotations inside of its ROI.
    EXCLUSIVE = 1 << 3,

    // Used to guarantee that when an anomalous annotation is added, its roi is
    // also given a global anomalous label
    ANOMALOUS = 1 << 4,
}

export interface Label {
    readonly id: string;
    readonly name: string;
    readonly color: string;
    readonly group: string;
    readonly parentLabelId: null | string;
    readonly hotkey?: string;
    readonly behaviour: LABEL_BEHAVIOUR;
    readonly isEmpty: boolean;
}

enum ShapeType {
    RotatedRect,
    Rect,
    Circle,
    Polygon,
    Pose,
}

export interface Point {
    x: number;
    y: number;
}

export interface Rect {
    readonly shapeType: ShapeType.Rect;
    readonly x: number;
    readonly y: number;
    readonly width: number;
    readonly height: number;
}

export interface Circle {
    readonly shapeType: ShapeType.Circle;
    readonly x: number;
    readonly y: number;
    readonly r: number;
}

export interface Polygon {
    readonly shapeType: ShapeType.Polygon;
    readonly points: Point[];
}

export interface RotatedRect {
    readonly shapeType: ShapeType.RotatedRect;
    readonly x: number;
    readonly y: number;
    readonly width: number;
    readonly height: number;
    readonly angle: number; //degrees
}

export interface KeypointNode extends Point {
    readonly label: Label;
    readonly isVisible: boolean;
}

export interface Pose {
    readonly shapeType: ShapeType.Pose;
    readonly points: KeypointNode[];
}

export type Shape = Rect | RotatedRect | Circle | Polygon | Pose;
