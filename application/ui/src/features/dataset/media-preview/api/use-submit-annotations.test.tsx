// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { type ReactNode } from 'react';

import type { AnnotationDTO, Label, Media, MediaDTO, MediaWithPagination } from '@/api/types';
import { InfiniteData, QueryClient } from '@tanstack/react-query';
import { act, waitFor } from '@testing-library/react';
import { getMockedShape } from 'mocks/mock-annotation';
import { getMockedAnnotationLabelRef, getMockedLabel } from 'mocks/mock-labels';
import { getMockedMediaImage, getMockedVideo, getMockedVideoFrame } from 'mocks/mock-media';
import { getMockedProject } from 'mocks/mock-project';
import { HttpResponse } from 'msw';

import { http } from '../../../../api/utils';
import {
    AnnotationDocumentProvider,
    useAnnotationCommands,
    useAnnotations,
} from '../../../../modules/annotator/annotation-document-provider.component';
import type { AnnotatorMode } from '../../../../modules/annotator/annotator-mode';
import { server } from '../../../../msw-node-setup';
import { createQueryClient } from '../../../../query-client/query-client';
import { EMPTY_LABEL_ID } from '../../../../shared/labels';
import { renderHook } from '../../../../test-utils/render';
import { useSubmitAnnotations } from './use-submit-annotations';

const renderSubmitAnnotations = ({
    initialAnnotationsDTO = [],
    initialPredictionsDTO = [],
    mediaItem = getMockedMediaImage(),
    mode = 'prediction' as AnnotatorMode,
    labels = [],
    queryClient,
}: {
    initialAnnotationsDTO?: AnnotationDTO[];
    initialPredictionsDTO?: AnnotationDTO[];
    mediaItem?: Media;
    mode?: AnnotatorMode;
    labels: Label[];
    queryClient?: QueryClient;
}) => {
    server.use(
        http.get('/api/projects/{project_id}', () =>
            HttpResponse.json(getMockedProject({ task: { task_type: 'detection', exclusive_labels: false, labels } }))
        )
    );

    const wrapper = ({ children }: { children: ReactNode }) => (
        <AnnotationDocumentProvider
            mode={mode}
            initialAnnotationsDTO={initialAnnotationsDTO}
            initialPredictionsDTO={initialPredictionsDTO}
        >
            {children}
        </AnnotationDocumentProvider>
    );

    return renderHook(
        () => ({ ...useAnnotations(), ...useAnnotationCommands(), ...useSubmitAnnotations({ mediaItem }) }),
        { wrapper, queryClient }
    );
};

describe('dataset media cache after submitting', () => {
    const mediaQueryKey = [
        'get',
        '/api/projects/{project_id}/dataset/media',
        { params: { path: { project_id: '123' }, query: { offset: 0, limit: 40 } } },
    ] as const;

    const createQueryClientWithMedia = (items: MediaDTO[]) => {
        const queryClient = createQueryClient();

        queryClient.setQueryData<InfiniteData<MediaWithPagination>>(mediaQueryKey, {
            pages: [{ items, pagination: { offset: 0, limit: 40, count: items.length, total: items.length } }],
            pageParams: [0],
        });

        return queryClient;
    };

    const getCachedMedia = (queryClient: QueryClient) =>
        queryClient.getQueryData<InfiniteData<MediaWithPagination>>(mediaQueryKey)?.pages[0].items;

    beforeEach(() => {
        server.use(
            http.post('/api/projects/{project_id}/dataset/media/{media_id}/annotations', () => HttpResponse.json({}))
        );
    });

    it('marks a submitted image as annotated', async () => {
        const image = getMockedMediaImage({ id: 'image-1', annotation_status: { has_annotations: false } });
        const queryClient = createQueryClientWithMedia([image]);

        const { result } = renderSubmitAnnotations({ mediaItem: image, mode: 'annotation', labels: [], queryClient });

        await waitFor(() => expect(result.current).not.toBeNull());
        await act(() => result.current.submit('unassigned'));

        expect(getCachedMedia(queryClient)).toEqual([{ ...image, annotation_status: { has_annotations: true } }]);
    });

    it("updates the video of a submitted frame with the server's annotated frame count", async () => {
        const video = getMockedVideo({
            id: 'video-1',
            annotation_status: { has_annotations: false, annotated_video_frames: 0 },
        });
        // The server is the source of truth: the count is not incremented locally, since the frame may have been
        // annotated already
        const refreshedVideo = { ...video, annotation_status: { has_annotations: true, annotated_video_frames: 2 } };
        const queryClient = createQueryClientWithMedia([video]);

        server.use(
            http.get('/api/projects/{project_id}/dataset/media/{media_id}', () => HttpResponse.json(refreshedVideo))
        );

        const { result } = renderSubmitAnnotations({
            mediaItem: getMockedVideoFrame({ id: video.id, frame_number: 3 }),
            mode: 'annotation',
            labels: [],
            queryClient,
        });

        await waitFor(() => expect(result.current).not.toBeNull());
        await act(() => result.current.submit('unassigned'));

        await waitFor(() => expect(getCachedMedia(queryClient)).toEqual([refreshedVideo]));
    });
});

describe('submit in prediction mode', () => {
    const label1 = getMockedLabel({ id: 'label-1', name: 'Cat', color: '#FF0000' });
    const label2 = getMockedLabel({ id: 'label-2', name: 'Dog', color: '#00FF00' });

    it('submits predictions with confidences stripped', async () => {
        const predictionsDTO: AnnotationDTO[] = [
            {
                labels: [{ id: label1.id }],
                shape: getMockedShape({ type: 'rectangle' }),
                confidences: [0.95],
            },
        ];

        let savedBody: { annotations: AnnotationDTO[]; subset?: string } | undefined;

        server.use(
            http.post('/api/projects/{project_id}/dataset/media/{media_id}/annotations', async ({ request }) => {
                savedBody = (await request.json()) as typeof savedBody;
                return HttpResponse.json({});
            })
        );

        const { result } = renderSubmitAnnotations({
            labels: [label1, label2],
            initialPredictionsDTO: predictionsDTO,
            mode: 'prediction',
        });

        await waitFor(() => expect(result.current).not.toBeNull());

        await act(async () => {
            await result.current.submit('training');
        });

        await waitFor(() => {
            expect(savedBody).toBeDefined();
            expect(savedBody?.annotations).toHaveLength(1);
            expect(savedBody?.annotations[0]).not.toHaveProperty('confidences');
            expect(savedBody?.annotations[0].labels).toEqual([{ id: label1.id }]);
        });
    });

    it('filters out annotations with empty labels', async () => {
        const predictionsDTO: AnnotationDTO[] = [
            { labels: [{ id: EMPTY_LABEL_ID }], shape: { type: 'full_image' } },
            { labels: [{ id: label1.id }], shape: getMockedShape({ type: 'rectangle' }) },
        ];

        let savedBody: { annotations: AnnotationDTO[] } | undefined;

        server.use(
            http.post('/api/projects/{project_id}/dataset/media/{media_id}/annotations', async ({ request }) => {
                savedBody = (await request.json()) as typeof savedBody;
                return HttpResponse.json({});
            })
        );

        const { result } = renderSubmitAnnotations({
            mode: 'prediction',
            labels: [label1, label2],
            initialPredictionsDTO: predictionsDTO,
        });

        await waitFor(() => expect(result.current).not.toBeNull());

        await act(() => result.current.submit('training'));

        await waitFor(() => {
            expect(savedBody).toBeDefined();
            expect(savedBody?.annotations).toHaveLength(1);
            expect(savedBody?.annotations[0].labels).toEqual([{ id: label1.id }]);
        });
    });
});

describe('Label normalization', () => {
    it('stores label refs (not full labels) when adding annotations', async () => {
        const label1 = getMockedLabel({ id: 'label-1', name: 'Cat', color: '#FF0000' });
        const { result } = renderSubmitAnnotations({ mode: 'annotation', labels: [label1] });

        await waitFor(() => expect(result.current).not.toBeNull());

        act(() => {
            result.current.addAnnotations([getMockedShape({ type: 'rectangle' })], [{ id: label1.id }]);
        });

        await waitFor(() => {
            expect(result.current.annotations).toHaveLength(1);
            expect(result.current.annotations[0].labels).toEqual([{ id: 'label-1' }]);
        });
    });

    it('annotation with no refs is invalid', async () => {
        const { result } = renderSubmitAnnotations({ mode: 'annotation', labels: [] });

        await waitFor(() => expect(result.current).not.toBeNull());

        act(() => {
            result.current.addAnnotations([getMockedShape({ type: 'rectangle' })], []);
        });

        await waitFor(() => {
            expect(result.current.annotations).toHaveLength(1);
            expect(result.current.annotations[0].labels).toEqual([]);
            expect(result.current.hasInvalidAnnotation).toBe(true);
            expect(result.current.canSubmit).toBe(false);
        });
    });

    it('filters unknown label ids when submitting annotations', async () => {
        const label1 = getMockedLabel({ id: 'label-1', name: 'Cat', color: '#FF0000' });
        const staleRef = getMockedAnnotationLabelRef({ id: 'deleted-label' });

        let savedBody: { annotations: AnnotationDTO[] } | undefined;

        server.use(
            http.post('/api/projects/{project_id}/dataset/media/{media_id}/annotations', async ({ request }) => {
                savedBody = (await request.json()) as typeof savedBody;
                return HttpResponse.json({});
            })
        );

        const { result } = renderSubmitAnnotations({ mode: 'annotation', labels: [label1] });

        await waitFor(() => expect(result.current).not.toBeNull());

        act(() => {
            result.current.addAnnotations([getMockedShape({ type: 'rectangle' })], [staleRef]);
        });

        await waitFor(() => expect(result.current.annotations).toHaveLength(1));

        await act(() => result.current.submit('training'));

        await waitFor(() => {
            expect(savedBody).toBeDefined();
            // Stale ref is filtered out at save time
            expect(savedBody?.annotations[0].labels).toEqual([]);
        });
    });
});

describe('canSubmit on initial load', () => {
    it('is false when initial annotations are unchanged, including a null confidences field from the server', async () => {
        const label1 = getMockedLabel({ id: 'label-1', name: 'Cat', color: '#FF0000' });

        // This is the exact shape the backend returns for a human annotation with no confidence
        // scores: `confidences` is present and `null` (see DatasetItemAnnotation), never omitted.
        const annotationsDTO: AnnotationDTO[] = [
            { labels: [{ id: label1.id }], shape: getMockedShape({ type: 'rectangle' }), confidences: null },
        ];

        const { result } = renderSubmitAnnotations({
            mode: 'annotation',
            labels: [label1],
            initialAnnotationsDTO: annotationsDTO,
        });

        await waitFor(() => expect(result.current).not.toBeNull());

        await waitFor(() => {
            expect(result.current.annotations).toHaveLength(1);
            expect(result.current.canSubmit).toBe(false);
        });
    });

    it('is true once an unchanged annotation set is actually edited', async () => {
        const label1 = getMockedLabel({ id: 'label-1', name: 'Cat', color: '#FF0000' });
        const label2 = getMockedLabel({ id: 'label-2', name: 'Dog', color: '#00FF00' });

        const annotationsDTO: AnnotationDTO[] = [
            { labels: [{ id: label1.id }], shape: getMockedShape({ type: 'rectangle' }), confidences: null },
        ];

        const { result } = renderSubmitAnnotations({
            mode: 'annotation',
            labels: [label1, label2],
            initialAnnotationsDTO: annotationsDTO,
        });

        await waitFor(() => expect(result.current.canSubmit).toBe(false));

        act(() => {
            result.current.addAnnotations([getMockedShape({ type: 'rectangle' })], [{ id: label2.id }]);
        });

        await waitFor(() => {
            expect(result.current.annotations).toHaveLength(2);
            expect(result.current.canSubmit).toBe(true);
        });
    });
});
