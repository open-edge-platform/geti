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
