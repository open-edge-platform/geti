// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { AnnotatedVideoFrame, AnnotationDTO } from '@/api/types';
import { waitFor } from '@testing-library/react';
import { getMockedVideoFrame } from 'mocks/mock-media';
import { HttpResponse } from 'msw';
import { renderHook } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { EMPTY_LABEL_ID } from '../../../../shared/labels';
import { useVideoFramesAnnotations } from './use-video-frames-annotations';

const mockVideoFrame = getMockedVideoFrame({ id: 'video-1', frame_count: 10, frame_number: 0 });

rs.mock('../video-player-provider.component', () => ({
    useVideoPlayer: () => ({ videoFrame: mockVideoFrame }),
}));

const getFrame = (frameIndex: number, annotations: AnnotationDTO[]): AnnotatedVideoFrame => ({
    media_id: 'video-1',
    frame_index: frameIndex,
    annotation_data: {
        annotations,
        user_reviewed: true,
        prediction_model_id: null,
        media_id: 'video-1',
        subset: 'training',
    },
});

const renderVideoFramesAnnotations = () =>
    renderHook(() => useVideoFramesAnnotations({ frameNumber: 0, frameSkip: 1, selector: (data) => data }));

describe('useVideoFramesAnnotations', () => {
    it('returns a full image annotation with the empty label for frames annotated with no annotations', async () => {
        server.use(
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/frames', () =>
                HttpResponse.json([getFrame(0, [])])
            )
        );

        const { result } = renderVideoFramesAnnotations();

        await waitFor(() => {
            expect(result.current.data?.[0].annotation_data.annotations).toEqual([
                { shape: { type: 'full_image' }, labels: [{ id: EMPTY_LABEL_ID }] },
            ]);
        });
    });

    it('keeps the annotations of annotated frames unchanged', async () => {
        const annotation: AnnotationDTO = {
            shape: { type: 'full_image' },
            labels: [{ id: 'label-a' }],
            confidences: null,
        };

        server.use(
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/frames', () =>
                HttpResponse.json([getFrame(0, [annotation])])
            )
        );

        const { result } = renderVideoFramesAnnotations();

        await waitFor(() => {
            expect(result.current.data?.[0].annotation_data.annotations).toEqual([annotation]);
        });
    });
});
