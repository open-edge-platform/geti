// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

export enum ACTION_TYPES {
    ENABLEMENT,
}

export interface CPRule {
    groupTitle: string;
    action: ACTION_TYPES.ENABLEMENT;
    switchFieldName: string;
    groupFields: string[];
}
export const CP_RULES: CPRule[] = [
    {
        groupTitle: 'Tiling',
        action: ACTION_TYPES.ENABLEMENT,
        switchFieldName: 'enable_tiling',
        groupFields: ['tile_max_number', 'tile_overlap', 'tile_sampling_ratio', 'tile_size'],
    },
];
