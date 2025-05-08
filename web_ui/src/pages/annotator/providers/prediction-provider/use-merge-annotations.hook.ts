// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isEmpty, mergeWith } from 'lodash-es';

import { Annotation, AnnotationLabel } from '../../../../core/annotations/annotation.interface';
import { recursivelyAddLabel } from '../../../../core/labels/label-resolver';
import { isExclusive } from '../../../../core/labels/utils';
import { hasEqualId } from '../../../../shared/utils';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { useImageROI } from '../../hooks/use-image-roi.hook';
import { getGlobalAnnotations, getLabelConflictPredicate } from '../task-chain-provider/utils';
import { useTask } from '../task-provider/task-provider.component';

interface MergeAnnotations {
    (newAnnotations: ReadonlyArray<Annotation>, oldAnnotations: ReadonlyArray<Annotation>): Annotation[];
}

const isExclusiveAnnotation = (annotation: Annotation) => annotation.labels.some(isExclusive);
const collectById = (annotations: Record<string, Annotation>, annotation: Annotation) => ({
    ...annotations,
    [annotation.id]: annotation,
});

const hasMultipleGlobalAnnotations =
    (newGlobalAnnotations: Annotation[], oldGlobalAnnotations: Annotation[]) => (oldAnnotation: Annotation) => {
        // We don't want to allow the user to have multiple global annotations, therefore
        // if they are merging a new global annotation we will remove any old global annotations
        if (!isEmpty(newGlobalAnnotations) && oldGlobalAnnotations.some(hasEqualId(oldAnnotation.id))) {
            return newGlobalAnnotations.some(hasEqualId(oldAnnotation.id));
        }
        return true;
    };

// This hook returns a function that allows us to merge annotations recursively if the
// new annotations contain annotations with the same id as an old annotation, then the
// shape will be replaced and labels will be merged
export const useMergeAnnotations = (): MergeAnnotations => {
    const { project } = useProject();
    const { selectedTask } = useTask();
    const roi = useImageROI();

    const mergeAnnotation = (originalAnnotation: Annotation | undefined, newAnnotation: Annotation | undefined) => {
        if (originalAnnotation === undefined) {
            return newAnnotation;
        }

        if (newAnnotation === undefined) {
            return originalAnnotation;
        }

        const conflictPredicate = getLabelConflictPredicate(project.tasks);
        const mergedLabels = newAnnotation.labels.reduce<ReadonlyArray<AnnotationLabel>>((labels, label) => {
            return recursivelyAddLabel(
                labels,
                label,
                project.labels,
                conflictPredicate
            ) as ReadonlyArray<AnnotationLabel>;
        }, originalAnnotation.labels);

        return {
            ...originalAnnotation,
            shape: newAnnotation.shape,
            labels: mergedLabels,
        };
    };

    const mergeAnnotations = (newAnnotations: ReadonlyArray<Annotation>, oldAnnotations: ReadonlyArray<Annotation>) => {
        const oldGlobalAnnotations = roi === undefined ? [] : getGlobalAnnotations(oldAnnotations, roi, selectedTask);
        const newGlobalAnnotations = roi === undefined ? [] : getGlobalAnnotations(newAnnotations, roi, selectedTask);
        const hasExclusiveAnnotations =
            newGlobalAnnotations.some(isExclusiveAnnotation) || oldGlobalAnnotations.some(isExclusiveAnnotation);

        const filteredOldGlobalAnnotations = oldAnnotations.filter(
            hasMultipleGlobalAnnotations(newGlobalAnnotations, oldGlobalAnnotations)
        );

        const filterOldNoObjectAnnotations = hasExclusiveAnnotations ? [] : filteredOldGlobalAnnotations;

        const newAnnotationsById: Record<string, Annotation> = newAnnotations.reduce(collectById, {});
        const oldAnnotationsById: Record<string, Annotation> = filterOldNoObjectAnnotations.reduce(collectById, {});

        return Object.values(mergeWith(oldAnnotationsById, newAnnotationsById, mergeAnnotation));
    };

    return mergeAnnotations;
};
