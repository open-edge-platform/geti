// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { fetchClient } from '@/api';
import type { AnnotationDTO, Media, Project } from '@/api/types';

import { mapLocalAnnotationsToServer } from '../../../shared/annotator/annotation-mappers';
import { getMediaBinaryUrl, getVideoFrameBinaryUrl } from '../../../shared/media-url.utils';
import {
    annotationInstructions,
    annotationTool,
    parseAnnotationProposal,
    type AnnotationTarget,
} from '../annotation/annotation-tools';
import { AI_SYSTEM_INSTRUCTION } from '../config';
import { getAiConnection } from '../connection';
import { loadMediaAttachment, type MediaAttachmentSource } from '../media-attachment';
import { assistantRespond, cancelAssistantResponse } from '../transport/assistant-transport';
import { AssistantConnectionError, type ResponsesItem } from '../types';

interface BatchWorkItem {
    key: string;
    mediaId: string;
    frameIndex: number | null;
    name: string;
    width: number;
    height: number;
    source: MediaAttachmentSource;
}

interface ExistingAnnotationState {
    annotations: AnnotationDTO[];
    isAnnotated: boolean;
}

export interface BatchAnnotationFailure {
    key: string;
    name: string;
    message: string;
}

export interface BatchAnnotationProgress {
    phase: 'preparing' | 'annotating';
    completed: number;
    total: number;
    succeeded: number;
    failed: number;
    skipped: number;
    annotationsAdded: number;
    current: string;
}

export interface BatchAnnotationResult {
    cancelled: boolean;
    completed: number;
    succeeded: number;
    failed: number;
    skipped: number;
    annotationsAdded: number;
    failures: BatchAnnotationFailure[];
}

interface BatchAnnotationOptions {
    projectId: string;
    project: Project;
    mediaIds: string[];
    signal: AbortSignal;
    onlyUnannotated: boolean;
    videoFramesPerSecond: VideoFramesPerSecond;
    onProgress: (progress: BatchAnnotationProgress) => void;
}

export type VideoFramesPerSecond = 1 | 2 | 5 | 10;

const abortError = () => new DOMException('The annotation run was cancelled.', 'AbortError');

const throwIfAborted = (signal: AbortSignal): void => {
    if (signal.aborted) throw abortError();
};

const isAbortError = (error: unknown): boolean =>
    (error instanceof DOMException && error.name === 'AbortError') ||
    (error instanceof Error && error.message === 'Stopped.');

const errorMessage = (error: unknown): string => {
    if (error instanceof Error) return error.message;
    if (typeof error === 'object' && error !== null && 'detail' in error) return String(error.detail);
    return 'The item could not be annotated.';
};

export const sampleVideoFrameIndexes = (
    frameCount: number,
    fps: number,
    framesPerSecond: VideoFramesPerSecond = 1
): number[] => {
    const sourceFps = Math.max(1, fps);
    const effectiveRate = Math.min(framesPerSecond, sourceFps);
    const indexes: number[] = [];

    // The existing annotations endpoint treats frame_index=0 as a missing
    // query parameter, so frame one is the first frame it can persist.
    for (let sample = 0; ; sample += 1) {
        const index = 1 + Math.round((sample * sourceFps) / effectiveRate);
        if (index >= frameCount) break;
        if (indexes.at(-1) !== index) indexes.push(index);
    }

    return indexes;
};

export const shouldSkipAlreadyAnnotated = (onlyUnannotated: boolean, isAnnotated: boolean): boolean =>
    onlyUnannotated && isAnnotated;

const workItemsForMedia = (
    projectId: string,
    media: Media,
    videoFramesPerSecond: VideoFramesPerSecond
): BatchWorkItem[] => {
    if (media.type !== 'video') {
        return [
            {
                key: media.id,
                mediaId: media.id,
                frameIndex: null,
                name: media.name,
                width: media.width,
                height: media.height,
                source: {
                    id: media.id,
                    name: media.name,
                    url: getMediaBinaryUrl(projectId, media.id),
                },
            },
        ];
    }

    const indexes = sampleVideoFrameIndexes(media.frame_count, media.fps, videoFramesPerSecond);
    if (indexes.length === 0) {
        throw new Error('The video has no frame that the annotations API can save.');
    }

    return indexes.map((frameIndex) => {
        const key = `${media.id}:${frameIndex}`;
        const name = `${media.name}, frame ${frameIndex}`;

        return {
            key,
            mediaId: media.id,
            frameIndex,
            name,
            width: media.width,
            height: media.height,
            source: {
                id: key,
                name,
                url: getVideoFrameBinaryUrl(projectId, media.id, frameIndex),
            },
        };
    });
};

const getMedia = async (projectId: string, mediaId: string): Promise<Media> => {
    const { data, error } = await fetchClient.GET('/api/projects/{project_id}/dataset/media/{media_id}', {
        params: { path: { project_id: projectId, media_id: mediaId } },
    });

    if (error !== undefined || data === undefined) throw error ?? new Error('The media item was not found.');

    return data as Media;
};

const getExistingAnnotations = async (projectId: string, item: BatchWorkItem): Promise<ExistingAnnotationState> => {
    if (item.frameIndex !== null) {
        const { data, error } = await fetchClient.GET('/api/projects/{project_id}/dataset/media/{media_id}/frames', {
            params: {
                path: { project_id: projectId, media_id: item.mediaId },
                query: { frame_index_from: item.frameIndex, frame_index_to: item.frameIndex },
            },
        });

        if (error !== undefined || data === undefined) {
            throw error ?? new Error('Existing frame annotations could not be read.');
        }

        const frame = data.find(({ frame_index }) => frame_index === item.frameIndex);
        return {
            annotations: frame?.annotation_data.annotations ?? [],
            isAnnotated: frame !== undefined,
        };
    }

    const { data: datasetItem, error: datasetItemError } = await fetchClient.GET(
        '/api/projects/{project_id}/dataset/items/{dataset_item_id}',
        {
            params: { path: { project_id: projectId, dataset_item_id: item.mediaId } },
        }
    );
    if (datasetItemError !== undefined || datasetItem === undefined) {
        throw datasetItemError ?? new Error('The dataset item could not be read.');
    }
    if (!datasetItem.user_reviewed) return { annotations: [], isAnnotated: false };

    const { data, error, response } = await fetchClient.GET(
        '/api/projects/{project_id}/dataset/media/{media_id}/annotations',
        {
            params: { path: { project_id: projectId, media_id: item.mediaId } },
        }
    );

    if (response.status === 404) return { annotations: [], isAnnotated: false };
    if (error !== undefined || data === undefined) throw error ?? new Error('Existing annotations could not be read.');

    return { annotations: data.annotations, isAnnotated: true };
};

const saveAnnotations = async (projectId: string, item: BatchWorkItem, annotations: AnnotationDTO[]): Promise<void> => {
    const query = item.frameIndex === null ? undefined : { frame_index: item.frameIndex };
    const { error } = await fetchClient.POST('/api/projects/{project_id}/dataset/media/{media_id}/annotations', {
        params: { path: { project_id: projectId, media_id: item.mediaId }, query },
        body: { annotations },
    });

    if (error !== undefined) throw error;
};

const requestProposals = async (
    project: Project,
    item: BatchWorkItem,
    signal: AbortSignal
): Promise<AnnotationDTO[]> => {
    throwIfAborted(signal);
    const target: AnnotationTarget = {
        key: item.key,
        width: item.width,
        height: item.height,
        taskType: project.task.task_type,
        exclusiveLabels: project.task.exclusive_labels,
        labels: project.task.labels ?? [],
        source: item.source,
        apply: () => undefined,
    };
    const attachment = await loadMediaAttachment(item.source, signal);
    const prompt = 'Annotate every visible object that matches a project label. Call propose_annotations now.';
    const input: ResponsesItem[] = [
        {
            type: 'message',
            role: 'user',
            content: [
                { type: 'input_text', text: prompt },
                { type: 'input_image', image_url: attachment.dataUrl, detail: 'high' },
            ],
        },
    ];
    const requestId = crypto.randomUUID();
    const cancel = () => cancelAssistantResponse(requestId);
    signal.addEventListener('abort', cancel, { once: true });

    try {
        const response = await assistantRespond({
            requestId,
            model: getAiConnection().model,
            instructions: `${AI_SYSTEM_INSTRUCTION}\n\n${annotationInstructions(target)}`,
            input,
            tools: [annotationTool(target)],
            onDelta: () => undefined,
        });
        throwIfAborted(signal);
        if (response.functionCalls.length === 0) {
            throw new Error('The assistant did not return an annotation proposal.');
        }
        const proposals = response.functionCalls.flatMap((call) => {
            if (call.name !== 'propose_annotations') throw new Error('The assistant returned an unsupported action.');
            const args: unknown = JSON.parse(call.arguments);
            if (typeof args !== 'object' || args === null || Array.isArray(args)) {
                throw new Error('The assistant returned an invalid annotation proposal.');
            }
            return parseAnnotationProposal(args as Record<string, unknown>, target);
        });

        return mapLocalAnnotationsToServer(proposals);
    } finally {
        signal.removeEventListener('abort', cancel);
    }
};

const emptyResult = (cancelled: boolean, failures: BatchAnnotationFailure[]): BatchAnnotationResult => ({
    cancelled,
    completed: failures.length,
    succeeded: 0,
    failed: failures.length,
    skipped: 0,
    annotationsAdded: 0,
    failures,
});

export const runBatchAnnotation = async ({
    projectId,
    project,
    mediaIds,
    signal,
    onlyUnannotated,
    videoFramesPerSecond,
    onProgress,
}: BatchAnnotationOptions): Promise<BatchAnnotationResult> => {
    const workItems: BatchWorkItem[] = [];
    const failures: BatchAnnotationFailure[] = [];

    for (const [index, mediaId] of mediaIds.entries()) {
        if (signal.aborted) return emptyResult(true, failures);
        onProgress({
            phase: 'preparing',
            completed: index,
            total: mediaIds.length,
            succeeded: 0,
            failed: failures.length,
            skipped: 0,
            annotationsAdded: 0,
            current: mediaId,
        });
        try {
            workItems.push(...workItemsForMedia(projectId, await getMedia(projectId, mediaId), videoFramesPerSecond));
        } catch (error) {
            failures.push({ key: mediaId, name: mediaId, message: errorMessage(error) });
        }
    }

    let completed = failures.length;
    let succeeded = 0;
    let skipped = 0;
    let annotationsAdded = 0;
    const total = workItems.length + failures.length;

    for (const item of workItems) {
        if (signal.aborted) {
            return {
                cancelled: true,
                completed,
                succeeded,
                failed: failures.length,
                skipped,
                annotationsAdded,
                failures,
            };
        }
        onProgress({
            phase: 'annotating',
            completed,
            total,
            succeeded,
            failed: failures.length,
            skipped,
            annotationsAdded,
            current: item.name,
        });
        try {
            const existing = await getExistingAnnotations(projectId, item);
            if (shouldSkipAlreadyAnnotated(onlyUnannotated, existing.isAnnotated)) {
                skipped += 1;
                completed += 1;
                continue;
            }
            const proposals = await requestProposals(project, item, signal);
            if (proposals.length > 0) await saveAnnotations(projectId, item, [...existing.annotations, ...proposals]);
            succeeded += 1;
            annotationsAdded += proposals.length;
        } catch (error) {
            if (isAbortError(error) || signal.aborted) {
                return {
                    cancelled: true,
                    completed,
                    succeeded,
                    failed: failures.length,
                    skipped,
                    annotationsAdded,
                    failures,
                };
            }
            failures.push({ key: item.key, name: item.name, message: errorMessage(error) });
            if (error instanceof AssistantConnectionError) {
                completed += 1;
                return {
                    cancelled: false,
                    completed,
                    succeeded,
                    failed: failures.length,
                    skipped,
                    annotationsAdded,
                    failures,
                };
            }
        }
        completed += 1;
    }

    onProgress({
        phase: 'annotating',
        completed,
        total,
        succeeded,
        failed: failures.length,
        skipped,
        annotationsAdded,
        current: '',
    });

    return {
        cancelled: false,
        completed,
        succeeded,
        failed: failures.length,
        skipped,
        annotationsAdded,
        failures,
    };
};
