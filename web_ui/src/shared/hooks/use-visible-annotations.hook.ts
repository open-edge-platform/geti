// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Annotation } from '../../core/annotations/annotation.interface';
import { isClassificationDomain } from '../../core/projects/domains';
import { useTask } from '../../pages/annotator/providers/task-provider/task-provider.component';

export const useVisibleAnnotations = (annotations: ReadonlyArray<Annotation>) => {
    const { selectedTask, tasks } = useTask();
    const isSingleClassification =
        selectedTask !== null && tasks.length === 1 && isClassificationDomain(selectedTask.domain);

    return annotations.map((annotation: Annotation) => {
        return isSingleClassification ? { ...annotation, isSelected: true } : annotation;
    });
};
