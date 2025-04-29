// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Annotation } from '../../../core/annotations/annotation.interface';
import { isClassificationDomain } from '../../../core/projects/domains';
import { hasEqualId } from '../../../shared/utils';
import { useIsPredictionRejected } from '../providers/annotation-threshold-provider/annotation-threshold-provider.component';
import { useROI } from '../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTaskChainOutput } from '../providers/task-chain-provider/use-task-chain-output.hook';
import { getGlobalAnnotations } from '../providers/task-chain-provider/utils';
import { useTask } from '../providers/task-provider/task-provider.component';

// Returns annotations shown in the annotation list
export const useLocalAnnotations = () => {
    const isPredictionRejected = useIsPredictionRejected();
    const { tasks, selectedTask } = useTask();
    const { roi } = useROI();
    const annotations = useTaskChainOutput(tasks, selectedTask);
    const globalAnnotations = getGlobalAnnotations(annotations, roi, selectedTask);

    const isTaskChainSelectedClassification =
        tasks.length > 1 && selectedTask !== null && isClassificationDomain(selectedTask.domain);

    // Normally we don't want to show global annotations in the annotation list,
    // which we filter them out here.
    // An edge case however is the classification task when the previous task was a
    // local task (i.e. detection). In this case we want to show each of the outputs
    return annotations.filter((annotation: Annotation) => {
        if (isPredictionRejected(annotation)) {
            return false;
        }

        if (isTaskChainSelectedClassification) {
            return true;
        }

        // Remove any global annotations that are considered to be outputs of this annotation
        return !globalAnnotations.some(hasEqualId(annotation.id));
    });
};
