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

import { Label, LABEL_BEHAVIOUR } from '../../../../core/labels/label.interface';
import { GrabcutToolType } from './grabcut-tool.enums';

export const isForegroundTool = (type: GrabcutToolType) => type === GrabcutToolType.ForegroundTool;
export const isBackgroundTool = (type: GrabcutToolType) => type === GrabcutToolType.BackgroundTool;

export const calcStrokeWidth = (rectWidth: number): number => {
    const percentage = rectWidth < 1000 ? 0.005 : 0.01;
    const minWidth = 4;
    const width = Math.round(rectWidth * percentage);
    return Math.max(minWidth, width);
};

export const sensitivityConfig = {
    min: 15,
    max: 35,
    step: 5,
    default: 20,
};

export const sensitivityOptions: { [key: number]: number } = {
    15: 1,
    20: 2,
    25: 3,
    30: 4,
    35: 5,
};

export const getLabel = (name: string, color: string): Label => ({
    name,
    color,
    id: '',
    group: '',
    hotkey: '',
    behaviour: LABEL_BEHAVIOUR.LOCAL,
    parentLabelId: '',
    isEmpty: false,
});
