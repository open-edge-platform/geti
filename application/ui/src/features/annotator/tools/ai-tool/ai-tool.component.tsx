// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useProject } from 'hooks/api/project.hook';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { useAnnotationActions } from '../../../../shared/annotator/annotation-actions-provider.component';
import { useTool } from '../../../../shared/annotator/tool-provider.component';
import { isVideoFrame } from '../../../../shared/media-item-utils';
import { getMediaBinaryUrl, getVideoFrameBinaryUrl } from '../../../../shared/media-url.utils';
import type { AnnotationTarget } from '../../../ai-assistant/annotation/annotation-tools';
import { AssistantDrawer } from '../../../ai-assistant/components/assistant-drawer.component';
import { useSelectedMediaItem } from '../../selected-media-item-provider.component';

export const AiTool = () => {
    const projectId = useProjectIdentifier();
    const { data: project } = useProject();
    const { mediaItem } = useSelectedMediaItem();
    const { appendAnnotations } = useAnnotationActions();
    const { setActiveTool } = useTool();
    const taskType = project.task.task_type;

    if (taskType !== 'detection' && taskType !== 'instance_segmentation') {
        return null;
    }

    const frameNumber = isVideoFrame(mediaItem) ? mediaItem.frame_number : null;
    const mediaKey = frameNumber === null ? mediaItem.id : `${mediaItem.id}:${frameNumber}`;
    const mediaName = frameNumber === null ? mediaItem.name : `${mediaItem.name}, frame ${frameNumber}`;
    const mediaUrl =
        frameNumber === null
            ? getMediaBinaryUrl(projectId, mediaItem.id)
            : getVideoFrameBinaryUrl(projectId, mediaItem.id, frameNumber);
    const target: AnnotationTarget = {
        key: mediaKey,
        width: mediaItem.width,
        height: mediaItem.height,
        taskType,
        exclusiveLabels: project.task.exclusive_labels,
        labels: project.task.labels ?? [],
        source: { id: mediaKey, name: mediaName, url: mediaUrl },
        apply: appendAnnotations,
    };

    return <AssistantDrawer target={target} onClose={() => setActiveTool(null)} />;
};
