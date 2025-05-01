// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isNotCropTask } from '@shared/utils';

import { fetchLabelsTree, fetchLabelsTreeWithGroups } from '../../../../core/labels/annotator-utils/labels-utils';
import {
    LabelItemEditionState,
    LabelTreeItem,
    LabelTreeLabelProps,
} from '../../../../core/labels/label-tree-view.interface';
import { Label, LabelsRelationType } from '../../../../core/labels/label.interface';
import { getNotEmptyLabelsFromOneTask } from '../../../../core/labels/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { Task, TaskMetadata } from '../../../../core/projects/task.interface';

export const getUnremovedLabels = (labelsTree: LabelTreeItem[]): LabelTreeItem[] => {
    return labelsTree.filter(({ state }) => state !== LabelItemEditionState.REMOVED);
};

export const getLabelsWithState = (
    flattenedLabels: LabelTreeLabelProps[],
    states: LabelItemEditionState[]
): LabelTreeLabelProps[] => {
    return flattenedLabels.filter(({ state }) => states.includes(state));
};

export const getRelation = (_labels: Label[], domains: DOMAIN[]): LabelsRelationType => {
    const [domain] = domains;

    if (domains.length > 1) {
        return LabelsRelationType.MIXED;
    }

    if (domain !== DOMAIN.CLASSIFICATION) {
        return LabelsRelationType.SINGLE_SELECTION;
    } else {
        return LabelsRelationType.MIXED;
    }
};

const getRelationNew = (_labels: Label[], domain: DOMAIN): LabelsRelationType => {
    if (domain !== DOMAIN.CLASSIFICATION) {
        return LabelsRelationType.SINGLE_SELECTION;
    } else {
        return LabelsRelationType.MIXED;
    }
};

const getLabelsTree = (
    relation: LabelsRelationType,
    labels: Label[],
    parentLabelId: string | null,
    parentGroup: string | null,
    level = 1
): LabelTreeItem[] => {
    if (relation === LabelsRelationType.MIXED) {
        return fetchLabelsTreeWithGroups(labels, 'all', parentLabelId, parentGroup, level);
    }

    return fetchLabelsTree(labels, 'all');
};

export const getTasksMetadata = (tasks: Task[], keepNoObjectLabels = false): TaskMetadata[] => {
    const filteredTasks = tasks.filter(isNotCropTask);

    return filteredTasks.map((task, index) => {
        const taskLabels = keepNoObjectLabels ? task.labels : [...getNotEmptyLabelsFromOneTask(task)];
        const parent = !!index ? filteredTasks[index - 1].labels[0] : undefined;
        const parentId = parent ? parent.id : null;
        const parentGroup = parent ? parent.group : null;
        const relation = getRelationNew(taskLabels, task.domain);

        return {
            labels: getLabelsTree(relation, taskLabels, parentId, parentGroup, index + 1),
            relation,
            domain: task.domain,
        };
    });
};
