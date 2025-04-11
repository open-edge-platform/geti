// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
