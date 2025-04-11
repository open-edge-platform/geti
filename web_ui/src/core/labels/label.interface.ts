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

interface LabelCommon {
    readonly name: string;
    readonly color: string;
    readonly group: string;
    readonly parentLabelId: null | string;
    readonly hotkey?: string;
    readonly behaviour: LABEL_BEHAVIOUR;
    readonly isEmpty: boolean;
}

export interface Label extends LabelCommon {
    readonly id: string;
}

interface NewLabel extends LabelCommon {
    revisitAffectedAnnotations: boolean;
}
export interface RevisitLabel extends Label {
    revisitAffectedAnnotations: boolean;
}

export interface DeletedLabel extends Label {
    isDeleted: boolean;
}

export type EditedLabel = Label | NewLabel | DeletedLabel | RevisitLabel;

export interface Group {
    name: string;
    id: string;
    parentLabelId: null | string;
    parentName: null | string;
}

export enum LABEL_BEHAVIOUR {
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

export enum LabelsRelationType {
    SINGLE_SELECTION = 'Single selection',
    MULTI_SELECTION = 'Multiple selection',
    MIXED = 'Mixed',
}
