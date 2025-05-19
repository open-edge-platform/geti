// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { negate } from 'lodash-es';

import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { KeypointNode, Point } from '../../../../core/annotations/shapes.interface';
import { LabelItemEditionState, LabelItemType, LabelTreeItem } from '../../../../core/labels/label-tree-view.interface';
import { LabelsRelationType } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { TaskMetadata } from '../../../../core/projects/task.interface';
import { DEFAULT_LABEL, getNextColor } from '../../../../shared/components/label-tree-view/utils';

export interface EdgeLine {
    id: string;
    from: KeypointNode;
    to: KeypointNode;
}

export interface TemplateState {
    edges: EdgeLine[];
    points: KeypointNode[];
}

export interface TemplateStateWithHistory extends TemplateState {
    skipHistory?: boolean;
}

export const isEqualLabel = (point: KeypointNode) => (otherPoint: KeypointNode) => {
    return point.label.id === otherPoint.label.id;
};

export const isDifferentLabel = (point: KeypointNode) => negate(isEqualLabel(point));

export const isMatchingEdge = (from: KeypointNode, to: KeypointNode) => (edge: EdgeLine) => {
    return isEqualLabel(edge.from)(from) && isEqualLabel(edge.to)(to);
};

export const isNotMatchingEdge = (from: KeypointNode, to: KeypointNode) => negate(isMatchingEdge(from, to));

export const isPointInEdge =
    (point: KeypointNode) =>
    ({ from, to }: EdgeLine): boolean => {
        return from.label.id === point.label.id || to.label.id === point.label.id;
    };

export const isEdgeConnectingPoints =
    (point: KeypointNode, otherPoint: KeypointNode) =>
    ({ from, to }: EdgeLine): boolean =>
        (from.label.id === point.label.id || from.label.id === otherPoint.label.id) &&
        (to.label.id === point.label.id || to.label.id === otherPoint.label.id);

export const getDefaultLabelStructure = (name: string) => {
    return DEFAULT_LABEL({
        name,
        color: getNextColor([]),
        groupName: '',
        relation: LabelsRelationType.SINGLE_SELECTION,
        parentLabelId: null,
    });
};

export const rgbToHex = (r: number, g: number, b: number): string => {
    const toHex = (component: number) => component.toString(16).padStart(2, '0');
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
};

export const getLabelFromPoint = (point: KeypointNode): LabelTreeItem => {
    return {
        ...point.label,
        open: false,
        inEditMode: false,
        children: [],
        type: LabelItemType.LABEL,
        state: LabelItemEditionState.IDLE,
        relation: LabelsRelationType.SINGLE_SELECTION,
    };
};

export const createRoi = (width?: number, height?: number): RegionOfInterest => {
    return {
        x: 0,
        y: 0,
        width: width ?? 0,
        height: height ?? 0,
    };
};

export const getProjectTypeMetadata = (
    points: KeypointNode[],
    edges: EdgeLine[],
    roi: RegionOfInterest
): TaskMetadata => {
    return {
        domain: DOMAIN.KEYPOINT_DETECTION,
        relation: LabelsRelationType.SINGLE_SELECTION,
        labels: points.map(getLabelFromPoint),
        keypointStructure: {
            edges: edges.map(({ from, to }) => ({ nodes: [from.label.name, to.label.name] })),
            positions: points.map(({ label, x, y }: KeypointNode) => {
                return {
                    label: label.name,
                    x: x / roi.width,
                    y: y / roi.height,
                };
            }),
        },
    };
};

export const updateWithLatestPoints =
    (points: KeypointNode[]) =>
    ({ id, from, to }: EdgeLine) => {
        return {
            id,
            to: points.find(isEqualLabel(to)) as KeypointNode,
            from: points.find(isEqualLabel(from)) as KeypointNode,
        };
    };

export const denormalizePoint = <T extends Point>(point: T, roi: RegionOfInterest): T => {
    return { ...point, x: point.x * roi.width, y: point.y * roi.height };
};
