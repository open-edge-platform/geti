// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { negate, overSome } from 'lodash-es';

import { idMatchingFormat } from '../../test-utils/id-utils';
import { AnnotationLabel } from '../annotations/annotation.interface';
import { DOMAIN } from '../projects/core.interface';
import { isAnomalyDomain, isClassificationDomain } from '../projects/domains';
import { Task } from '../projects/task.interface';
import { DeletedLabelDTO, LabelDTO, NewLabelDTO } from './dtos/label.interface';
import { LabelItemType, LabelTreeGroupProps, LabelTreeItem, LabelTreeLabelProps } from './label-tree-view.interface';
import { DeletedLabel, Label, LABEL_BEHAVIOUR } from './label.interface';

export const getFlattenedItems = (currentLabels: LabelTreeItem[]): LabelTreeItem[] => {
    if (currentLabels.length === 0) {
        return [];
    }

    return currentLabels.reduce((previous: LabelTreeItem[], current: LabelTreeItem) => {
        return previous.concat([current]).concat(getFlattenedItems(current.children));
    }, []);
};

export const onlyLabelsFilter = (item: LabelTreeItem): item is LabelTreeLabelProps => {
    return item.type === LabelItemType.LABEL;
};
const onlyGroupsFilter = (item: LabelTreeItem): item is LabelTreeGroupProps => {
    return item.type === LabelItemType.GROUP;
};

export const filterGroups = (flattenedItems: LabelTreeItem[]): LabelTreeGroupProps[] => {
    return flattenedItems.filter(onlyGroupsFilter);
};

export const filterLabels = (flattenedItems: LabelTreeItem[]): LabelTreeLabelProps[] => {
    return flattenedItems.filter(onlyLabelsFilter);
};

export const getFlattenedLabels = (labelsTree: LabelTreeItem[]): LabelTreeLabelProps[] => {
    return getFlattenedItems(labelsTree).filter(onlyLabelsFilter) as LabelTreeLabelProps[];
};

export const getFlattenedGroups = (labelsTree: LabelTreeItem[]): LabelTreeGroupProps[] => {
    return filterGroups(getFlattenedItems(labelsTree));
};

export const isExclusive = (label: { behaviour: LABEL_BEHAVIOUR }): boolean => {
    return Boolean(label.behaviour & LABEL_BEHAVIOUR.EXCLUSIVE);
};

export const isLocal = (label: Label): boolean => {
    return Boolean(label.behaviour & LABEL_BEHAVIOUR.LOCAL);
};

export const isGlobal = (label: Label): boolean => {
    return Boolean(label.behaviour & LABEL_BEHAVIOUR.GLOBAL) || isExclusive(label);
};

export const isAnomalous = <T extends { behaviour: LABEL_BEHAVIOUR }>(label: T): boolean => {
    return Boolean(label.behaviour & LABEL_BEHAVIOUR.ANOMALOUS);
};

export const isBackgroundBehavior = <T extends { behaviour: LABEL_BEHAVIOUR }>(label: T): boolean => {
    return Boolean(label.behaviour & LABEL_BEHAVIOUR.BACKGROUND);
};

interface EmptyOrBackground {
    isEmpty: boolean;
    behaviour: LABEL_BEHAVIOUR;
}

export const isEmptyLabel = <T extends EmptyOrBackground>(label: T): boolean => label.isEmpty;
export const isNonEmptyLabel = negate(isEmptyLabel);

export const isBackgroundLabel = <T extends EmptyOrBackground>(label: T): boolean => {
    return isBackgroundBehavior(label);
};

export const isNonBackgroundLabel = negate(isBackgroundLabel);

export const isEmptyOrBackgroundLabel = overSome([isEmptyLabel, isBackgroundLabel]);

export const filterOutEmptyLabel = (labels: readonly Label[]): readonly Label[] => labels.filter(isNonEmptyLabel);

export const filterOutEmptyAndBackgroundLabel = (labels: readonly Label[]): readonly Label[] =>
    labels.filter((label) => isNonEmptyLabel(label) && isNonBackgroundLabel(label));

// Predictions come from a model but are not yet accepted (userId).
export const isPrediction = (label?: AnnotationLabel) =>
    label?.score !== undefined && label.source.userId === undefined;

// We want to show the label score when:
// 1) The label comes from a model (it is a prediction label)
// 2) The label is NOT exclusive ("Empty", "No class", "No object")
// 3) The label is "Normal" or "Anomalous"
export const showLabelScore = (label: AnnotationLabel, domain?: DOMAIN): boolean => {
    return isPrediction(label) && (!isExclusive(label) || (isExclusive(label) && !!domain && isAnomalyDomain(domain)));
};

export const getBehaviourFromDTO = (
    label: LabelDTO | NewLabelDTO | DeletedLabelDTO,
    domain: DOMAIN
): LABEL_BEHAVIOUR => {
    /* new label does not have this parameter - it cannot be anomalous */
    const isAnomalousLabel = 'is_anomalous' in label && label.is_anomalous;

    const labelIsEmpty = isAnomalyDomain(domain) && !isAnomalousLabel ? true : label.is_empty;

    if (labelIsEmpty) {
        return LABEL_BEHAVIOUR.EXCLUSIVE + LABEL_BEHAVIOUR.GLOBAL;
    }

    if (isAnomalyDomain(domain)) {
        if (isAnomalousLabel) {
            return LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.ANOMALOUS;
        }
    }

    if (isClassificationDomain(domain)) {
        return LABEL_BEHAVIOUR.GLOBAL;
    }

    if (label.is_background) {
        return LABEL_BEHAVIOUR.BACKGROUND;
    }

    return LABEL_BEHAVIOUR.LOCAL;
};

export const GROUP_SEPARATOR = '___';

export const getLabelId = (namespace: string, label: Label | undefined): string => {
    if (!label) {
        return '';
    }

    const prefix: string[] = ['label', namespace];
    const suffix: string[] = [...label.name.split(' '), idMatchingFormat(label.name)];

    return [...prefix, ...suffix]
        .join('-')
        .replace(/[\s_]+/g, '-')
        .toLowerCase();
};

export const getNewLabelPayload = (label: LabelTreeLabelProps, revisit: boolean) => {
    const { name, color, hotkey, group, behaviour, parentLabelId } = label;

    return {
        revisitAffectedAnnotations: revisit,
        name,
        color,
        hotkey,
        group,
        parentLabelId,
        behaviour,
        isEmpty: false,
    };
};

export const getDeletedLabelPayload = (label: LabelTreeLabelProps): DeletedLabel => {
    const { name, color, hotkey, group, behaviour, parentLabelId, id, isEmpty } = label;

    return {
        id,
        name,
        color,
        hotkey,
        group,
        parentLabelId,
        behaviour,
        isDeleted: true,
        isEmpty,
    };
};

export const getLabelPayload = (label: LabelTreeLabelProps): Label => {
    const { id, name, color, hotkey, group, parentLabelId, behaviour, isEmpty } = label;

    return {
        id,
        name,
        color,
        hotkey,
        group,
        parentLabelId,
        behaviour,
        isEmpty,
    };
};

export const filterOutExclusiveLabel = (labels: readonly Label[]): readonly Label[] =>
    labels.filter(negate(isExclusive));

export const getNonEmptyLabelsFromProject = (tasks: Task[]): Label[] => {
    return tasks.flatMap(getNotEmptyLabelsFromOneTask);
};

export const getNotEmptyLabelsFromOneTask = (task: Task): readonly Label[] => {
    return filterOutEmptyLabel(task.labels);
};
