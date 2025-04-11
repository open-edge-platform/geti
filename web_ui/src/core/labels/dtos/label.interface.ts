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
    name: string;
    color: string;
    group: string;
    hotkey?: string;
    is_empty: boolean;
    parent_id: string | null;
}

export type LabelCreation = Omit<LabelCommon, 'is_empty'>;

export interface LabelDTO extends LabelCommon {
    id: string;
    is_anomalous: boolean;
}

export interface NewLabelDTO extends LabelCommon {
    revisit_affected_annotations: boolean;
}

export interface RevisitLabelDTO extends LabelCommon {
    id: string;
    revisit_affected_annotations: boolean;
}

export interface DeletedLabelDTO extends LabelDTO {
    is_deleted: boolean;
}
export type EditedLabelDTO = DeletedLabelDTO | RevisitLabelDTO | NewLabelDTO | LabelDTO;
