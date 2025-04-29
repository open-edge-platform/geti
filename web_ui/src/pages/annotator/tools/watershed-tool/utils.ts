// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { v4 as uuidv4 } from 'uuid';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { Shape } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../../../core/annotations/utils';
import { Label, LABEL_BEHAVIOUR } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { getLabeledShape } from '../../utils';
import { WatershedPolygon } from './watershed-tool.interface';

export const WATERSHED_SUPPORTED_DOMAINS = [
    DOMAIN.SEGMENTATION,
    DOMAIN.SEGMENTATION_INSTANCE,
    DOMAIN.ANOMALY_SEGMENTATION,
];

export const BACKGROUND_LABEL_MARKER_ID = 1;
const BACKGROUND_LABEL_ID = uuidv4();

export const CURSOR_OFFSET = `7 8`;
export const MINUS_OFFSET = '2 8';

export const BACKGROUND_LABEL: Label = {
    id: BACKGROUND_LABEL_ID,
    name: 'Background',
    color: 'var(--spectrum-global-color-gray-500)',
    parentLabelId: '',
    group: '',
    behaviour: LABEL_BEHAVIOUR.LOCAL,
    hotkey: 'ctrl+b',
    isEmpty: false,
};

const SENSITIVITY_CONFIG: number[] = [484, 1024, 1764, 2704, 4900];

export const getScaleValue = (sensitivity: number): number => {
    const config = SENSITIVITY_CONFIG[sensitivity];
    return config || SENSITIVITY_CONFIG[1];
};

export const SENSITIVITY_SLIDER_CONFIG = {
    defaultValue: 2,
    step: 1,
    min: 1,
    max: 5,
};

export const brushSizeSliderConfig = {
    defaultValue: 4,
    min: 1,
    max: 128,
    step: 1,
};

const formatToPolygonShapesWithLabel = (watershedPolygons: WatershedPolygon[]): [Shape, Label][] => {
    return watershedPolygons.map((polygon) => [
        { shapeType: ShapeType.Polygon, points: polygon.points },
        polygon.label,
    ]);
};

export const formatAndAddAnnotations = (
    watershedPolygons: WatershedPolygon[],
    addAnnotations: (annotations: Annotation[]) => void
): Annotation[] => {
    const newAnnotations = formatToPolygonShapesWithLabel(watershedPolygons).map(([shape, label], index) => {
        return getLabeledShape(uuidv4(), shape, [labelFromUser(label)], false, index);
    });

    addAnnotations(newAnnotations);

    return newAnnotations;
};

export const getMaxSensitivityForImage = (image: ImageData): number => {
    const highestSide = Math.max(image.width, image.height);
    const highest = SENSITIVITY_CONFIG.findIndex((scaleValue) => highestSide < scaleValue);

    return highest >= 0 ? highest + 1 : SENSITIVITY_CONFIG.length;
};
