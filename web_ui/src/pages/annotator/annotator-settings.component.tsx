// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
