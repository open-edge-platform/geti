// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
    isBackground: false,
});
