// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Label } from '../labels/label.interface';
import { Pose, Shape } from './shapes.interface';

export interface RegionOfInterest {
    x: number;
    y: number;
    width: number;
    height: number;
}

export interface AnnotationLabel extends Label {
    readonly source: {
        userId?: string;
        modelId?: string;
        modelStorageId?: string;
    };
    readonly score?: number;
}

export interface Annotation {
    readonly id: string;
    readonly labels: ReadonlyArray<AnnotationLabel>;
    readonly shape: Shape;
    readonly zIndex: number;
    readonly isSelected: boolean;
    readonly isHidden: boolean;
    readonly isLocked: boolean;
}

export type TaskChainInput = Annotation & { outputs: Annotation[] };

export type KeypointAnnotation = Annotation & { shape: Pose };
