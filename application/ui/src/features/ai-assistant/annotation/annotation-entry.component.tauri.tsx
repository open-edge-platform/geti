// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useRef, useState } from 'react';

import { Button } from '@geti-ui/ui';
import { useProject } from 'hooks/api/project.hook';
import { createPortal } from 'react-dom';
import { useLocation, useNavigate } from 'react-router-dom';

import { useAnnotationActions } from '../../../shared/annotator/annotation-actions-provider.component';
import { EMPTY_LABEL_ID } from '../../../shared/annotator/labels';
import { useTool } from '../../../shared/annotator/tool-provider.component';
import { isVideoFrame } from '../../../shared/media-item-utils';
import { getMediaDownloadUrl, getVideoFrameBinaryUrl } from '../../../shared/media-url.utils';
import { AssistantDrawer } from '../../ai-assistant/components/assistant-drawer.component';
import { useIsAnnotatorSceneBusy } from '../../annotator/hooks/use-is-annotator-scene-busy';
import { useSelectedMediaItem } from '../../annotator/selected-media-item-provider.component';
import { isAssistantAvailable } from '../platform';
import { annotationMediaKey, useAnnotationReview } from './annotation-review-provider.component';
import type { AnnotationTarget } from './annotation-tools';

export const ChatGptAnnotationButton = () => {
    const { data: project } = useProject();
    const { mediaItem, isImageReady } = useSelectedMediaItem();
    const actions = useAnnotationActions();
    const review = useAnnotationReview();
    const projectLabels = project.task.labels ?? [];
    const isPlaying = useIsAnnotatorSceneBusy();
    const { setActiveTool } = useTool();
    const location = useLocation();
    const navigate = useNavigate();
    const routeState: unknown = location.state;
    const openRequested =
        typeof routeState === 'object' &&
        routeState !== null &&
        'annotateWithChatGpt' in routeState &&
        routeState.annotateWithChatGpt === mediaItem.id;
    const [isOpen, setIsOpen] = useState(openRequested);
    useEffect(() => {
        if (openRequested) {
            setActiveTool('selection');
            setIsOpen(true);
            navigate({ pathname: location.pathname, search: location.search }, { replace: true, state: null });
        }
    }, [openRequested, location.pathname, location.search, navigate, setActiveTool]);
    const key = annotationMediaKey(project.id, mediaItem);
    const latest = useRef({ key, actions, isPlaying, labels: projectLabels });
    latest.current = { key, actions, isPlaying, labels: projectLabels };
    const source = {
        id: key,
        name: `${mediaItem.name}${isVideoFrame(mediaItem) ? ` · frame ${mediaItem.frame_number}` : ''}`,
        url: isVideoFrame(mediaItem)
            ? getVideoFrameBinaryUrl(project.id, mediaItem.id, mediaItem.frame_number)
            : getMediaDownloadUrl(project.id, mediaItem.id),
    };
    const target: AnnotationTarget = {
        key,
        source,
        width: mediaItem.width,
        height: mediaItem.height,
        taskType: project.task.task_type,
        exclusiveLabels: project.task.exclusive_labels,
        labels: projectLabels,
        apply: (proposals) => {
            const current = latest.current;
            if (current.key !== key || current.isPlaying || current.actions.isReadOnlyMode || current.actions.isSaving)
                throw new Error('The image changed or is busy. Generate annotations again.');
            const validIds = new Set(current.labels.map(({ id }) => id));
            if (proposals.some(({ labels }) => labels.some(({ id }) => !validIds.has(id))))
                throw new Error('Project labels changed. Generate annotations again.');
            if (proposals.length === 0) return;
            // One update preserves the editor's normal Undo/Redo and save workflow.
            current.actions.replaceAnnotations((annotations) => {
                const existing = annotations.filter(({ labels }) => labels.every(({ id }) => id !== EMPTY_LABEL_ID));
                return project.task.task_type === 'classification' ? proposals : [...existing, ...proposals];
            });
        },
    };
    if (!isAssistantAvailable()) return null;
    return (
        <>
            {!isOpen && (
                <Button
                    variant={'secondary'}
                    isDisabled={
                        !isImageReady ||
                        isPlaying ||
                        actions.isSaving ||
                        actions.isReadOnlyMode ||
                        projectLabels.length === 0
                    }
                    onPress={() => {
                        setActiveTool('selection');
                        setIsOpen(true);
                    }}
                >
                    Annotate with ChatGPT
                </Button>
            )}
            {isOpen &&
                !isPlaying &&
                review?.panelHost &&
                createPortal(
                    <AssistantDrawer
                        key={key}
                        projectId={project.id}
                        annotationTarget={target}
                        attachmentSources={[source]}
                        onClose={() => setIsOpen(false)}
                    />,
                    review.panelHost
                )}
        </>
    );
};
