// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Task } from '@/api/types';

export const getFormatOptions = (task: Task) => {
    // The YOLO classification format stores each image in the folder of a single class, so it is
    // only offered for single-label (multiclass) classification projects.
    const classificationOptions = task.exclusive_labels
        ? [
              { label: 'Geti', value: 'geti' },
              { label: 'VOC', value: 'voc' },
              { label: 'YOLO', value: 'yolo_cls' },
          ]
        : [
              { label: 'Geti', value: 'geti' },
              { label: 'VOC', value: 'voc' },
          ];

    const options: Record<Task['task_type'], { label: string; value: string }[]> = {
        classification: classificationOptions,
        instance_segmentation: [
            { label: 'Geti', value: 'geti' },
            { label: 'COCO', value: 'coco' },
            { label: 'YOLO', value: 'yolo_seg' },
        ],
        detection: [
            { label: 'Geti', value: 'geti' },
            { label: 'YOLO', value: 'yolo' },
            { label: 'COCO', value: 'coco' },
        ],
    };

    return options[task.task_type];
};
