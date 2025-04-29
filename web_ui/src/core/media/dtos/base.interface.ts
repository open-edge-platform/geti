// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
