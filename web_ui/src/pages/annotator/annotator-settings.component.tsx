// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { CSSProperties, ReactNode } from 'react';

import { CANVAS_ADJUSTMENTS_KEYS } from '../../core/user-settings/dtos/user-settings.interface';
import { useAnnotatorCanvasSettings } from './providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component';
import { getPercentage } from './utils';

interface AnnotatorCanvasSettingsProps {
    children: ReactNode;
}

export const AnnotatorCanvasSettings = ({ children }: AnnotatorCanvasSettingsProps) => {
    const { canvasSettingsState } = useAnnotatorCanvasSettings();
    const [canvasSettings] = canvasSettingsState;

    const canvasAdjustments = {
        '--label-opacity': canvasSettings[CANVAS_ADJUSTMENTS_KEYS.LABEL_OPACITY].value,
        '--markers-opacity': canvasSettings[CANVAS_ADJUSTMENTS_KEYS.MARKERS_OPACITY].value,
        '--annotation-fill-opacity': canvasSettings[CANVAS_ADJUSTMENTS_KEYS.ANNOTATION_FILL_OPACITY].value,
        '--annotation-border-opacity': canvasSettings[CANVAS_ADJUSTMENTS_KEYS.ANNOTATION_BORDER_OPACITY].value,
        '--image-brightness': getPercentage(Number(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.IMAGE_BRIGHTNESS].value)),
        '--image-contrast': getPercentage(Number(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.IMAGE_CONTRAST].value)),
        '--image-saturation': getPercentage(Number(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.IMAGE_SATURATION].value)),
        '--pixel-view': Boolean(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.PIXEL_VIEW].value) ? 'pixelated' : 'auto',
        height: '100%',
    } as CSSProperties;

    return <div style={canvasAdjustments}>{children}</div>;
};
