// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from '@adobe/react-spectrum';
import { isEqual, isNil } from 'lodash-es';
import { v4 as uuidv4 } from 'uuid';

import { RegionOfInterest } from '../../../../../core/annotations/annotation.interface';
import { KeypointNode } from '../../../../../core/annotations/shapes.interface';
import { denormalizePoint, EdgeLine, getDefaultLabelStructure, TemplateState } from '../util';

export interface RawStructure {
    points: { label: string; x: number; y: number }[];
    edges: { to: string; from: string }[];
}

export interface RawTemplate {
    name: string;
    template: RawStructure;
}

export enum TemplatePose {
    HumanPose = 'Human pose',
    HumanFace = 'Human face',
    AnimalPose = 'Animal pose',
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

const PROJECT_TEMPLATE_SUFFIX = 'project-template';
const GETI_TEMPLATE_SUFFIX = 'geti-template';

export const isProjectTemplate = (name: Key): name is string => String(name).startsWith(PROJECT_TEMPLATE_SUFFIX);
export const isGetiTemplate = (name: Key): name is string => String(name).startsWith(GETI_TEMPLATE_SUFFIX);

export const getProjectTemplateKey = (name: string) => `${PROJECT_TEMPLATE_SUFFIX}-${name}`;
export const getGetiTemplateKey = (name: string) => `${GETI_TEMPLATE_SUFFIX}-${name}`;

export const getProjectTemplateName = (name: string) => name.replaceAll(`${PROJECT_TEMPLATE_SUFFIX}-`, '');
export const getGetiTemplateName = (name: string) => name.replaceAll(`${GETI_TEMPLATE_SUFFIX}-`, '') as TemplatePose;
