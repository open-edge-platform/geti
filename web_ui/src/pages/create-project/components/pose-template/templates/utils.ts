// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isEqual from 'lodash/isEqual';
import isNil from 'lodash/isNil';
import { v4 as uuidv4 } from 'uuid';

import { RegionOfInterest } from '../../../../../core/annotations/annotation.interface';
import { KeypointNode } from '../../../../../core/annotations/shapes.interface';
import { denormalizePoint, EdgeLine, getDefaultLabelStructure, TemplateState } from '../util';

export interface RawStructure {
    points: { label: string; x: number; y: number }[];
    edges: { to: string; from: string }[];
}

export const formatTemplate = (structure: RawStructure, roi: RegionOfInterest): TemplateState => {
    const points = structure.points.map(
        (point): KeypointNode =>
            denormalizePoint({ ...point, isVisible: true, label: getDefaultLabelStructure(point.label) }, roi)
    );

    const edges = structure.edges
        .map((edge) => {
            const toNode = points.find((point) => point.label.name === edge.to);
            const fromNode = points.find((point) => point.label.name === edge.from);
            const isInvalidEdge = isNil(fromNode) || isNil(toNode) || isEqual(fromNode, toNode);

            if (isInvalidEdge) {
                return null;
            }

            return { id: uuidv4(), from: fromNode, to: toNode };
        })
        .filter(Boolean) as EdgeLine[];

    return { points, edges };
};
