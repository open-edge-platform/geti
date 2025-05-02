// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isEmpty from 'lodash/isEmpty';

import { getIds, hasEqualId } from '../../shared/utils';
import { Label } from './label.interface';
import { isExclusive } from './utils';

function labelsIncludingParent(
    annotationLabels: ReadonlyArray<Label>,
    label: Label,
    projectLabels: ReadonlyArray<Label>
): ReadonlyArray<Label> {
    const parentLabel = projectLabels.find(hasEqualId(label.parentLabelId));

    if (parentLabel === undefined || annotationLabels.some(hasEqualId(parentLabel.id))) {
        return annotationLabels;
    }

    return recursivelyAddLabel(annotationLabels, parentLabel, projectLabels);
}

const labelsConflictPredicate = (label: Label, otherLabel: Label) => {
    return label.group === otherLabel.group || isExclusive(label) || isExclusive(otherLabel);
};

/**
 * Add a label to an annotation.  If the label has a parent it is added as well.
 * Any conflicting labels (those in the same group as the new label) will be removed.
 */
export function recursivelyAddLabel(
    annotationLabels: ReadonlyArray<Label>,
    label: Label,
    projectLabels: ReadonlyArray<Label>,
    conflictPredicate: (label: Label, otherLabel: Label) => boolean = labelsConflictPredicate
): ReadonlyArray<Label> {
    // Do nothing if this label already exists
    if (annotationLabels.some(hasEqualId(label.id))) {
        return annotationLabels;
    }

    const shapeLabels = labelsIncludingParent(annotationLabels, label, projectLabels);

    const conflictingLabels = shapeLabels.filter((otherLabel) => conflictPredicate(label, otherLabel));

    return [...recursivelyRemoveLabels(shapeLabels, conflictingLabels), label];
}

/**
 * Remove labels from a list including any labels whose parents were removed.
 */
export function recursivelyRemoveLabels(
    annotationLabels: ReadonlyArray<Label>,
    labels: ReadonlyArray<Label>
): ReadonlyArray<Label> {
    // For each label that we want to remove, find their child labels
    const childLabels = annotationLabels.filter(({ parentLabelId }) => {
        return labels.some(hasEqualId(parentLabelId));
    });

    // Remove the child labels
    const labelsWithoutChildren = isEmpty(childLabels)
        ? annotationLabels
        : recursivelyRemoveLabels(annotationLabels, childLabels);

    const labelIds = getIds([...labels]);

    return labelsWithoutChildren.filter(({ id }) => !labelIds.includes(id));
}
