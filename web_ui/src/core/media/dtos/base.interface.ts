// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { MEDIA_ANNOTATION_STATUS } from '../base.interface';

export interface AnnotationStatePerTaskDTO {
    task_id: string;
    state: MEDIA_ANNOTATION_STATUS;
}

export interface BaseMediaDTO {
    id: string;
    name: string;
    state: MEDIA_ANNOTATION_STATUS;
    thumbnail: string;
    upload_time: string;
    uploader_id: string;
    annotation_state_per_task: AnnotationStatePerTaskDTO[];
    annotation_scene_id?: string;
    last_annotator_id: string | null;
}
