// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { AnnotatedVideoFrame } from '@/api/types';
import { DialogContainer } from '@geti-ui/ui';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { getMockedVideo } from 'mocks/mock-media';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { MediaDetails } from './media-details.component';

rs.mock('hooks/use-project-identifier.hook', () => ({ useProjectIdentifier: () => 'project-123' }));

const getValue = (label: string) => screen.getByText(label, { selector: 'dt' }).nextElementSibling;

describe('MediaDetails', () => {
    it('shows video metadata, retries annotation loading across all frames and closes', async () => {
        const user = userEvent.setup();
        const onClose = rs.fn();
        const requestedRange = rs.fn();
        const item = getMockedVideo({
            name: 'boxes.v2',
            format: 'mp4',
            width: 1920,
            height: 1080,
            size: 1500000,
            fps: 29.97,
            duration: 12.5,
            frame_count: 400,
            annotation_status: { has_annotations: true, annotated_video_frames: 1 },
        });
        const frames: AnnotatedVideoFrame[] = [
            {
                media_id: 'frame-399',
                frame_index: 399,
                annotation_data: {
                    annotations: [
                        { shape: { type: 'full_image' }, labels: [{ id: 'label-1' }] },
                        { shape: { type: 'full_image' }, labels: [{ id: 'label-1' }] },
                    ],
                    user_reviewed: true,
                    subset: 'training',
                },
            },
        ];
        server.use(
            http.get(
                '/api/projects/{project_id}/dataset/media/{media_id}/frames',
                () => new HttpResponse(null, { status: 500 })
            )
        );
        render(
            <DialogContainer onDismiss={onClose}>
                <MediaDetails item={item} onClose={onClose} />
            </DialogContainer>
        );

        expect(screen.getByRole('dialog', { name: 'Details' })).toBeVisible();
        expect(screen.getByRole('heading', { name: 'boxes.v2.mp4' })).toHaveAttribute('title', 'boxes.v2.mp4');
        expect(screen.getByRole('img')).toHaveAttribute(
            'src',
            expect.stringContaining(`/api/projects/project-123/dataset/media/${item.id}/thumbnail`)
        );
        expect(getValue('Annotations')).toHaveTextContent('Loading...');
        await waitFor(() => expect(getValue('Annotations')).toHaveTextContent('Unavailable'));
        expect(screen.getByRole('status')).toHaveTextContent('Annotated');
        expect(getValue('Annotated frames')).toHaveTextContent('1');

        server.use(
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/frames', ({ request }) => {
                const params = new URL(request.url).searchParams;
                requestedRange(params.get('frame_index_from'), params.get('frame_index_to'));
                const from = Number(params.get('frame_index_from') ?? 0);
                const to = Number(params.get('frame_index_to') ?? 50);
                return HttpResponse.json(
                    frames.filter((frame) => frame.frame_index >= from && frame.frame_index <= to)
                );
            })
        );
        await user.click(screen.getByRole('button', { name: 'Retry' }));
        await waitFor(() => expect(getValue('Annotations')).toHaveTextContent('2'));
        expect(getValue('Unique labels')).toHaveTextContent('1');
        expect(requestedRange).toHaveBeenCalledWith('0', '399');
        expect(getValue('Resolution')).toHaveTextContent('1920 × 1080 px');
        expect(getValue('File size')).toHaveTextContent('1.5 MB');
        expect(getValue('Format')).toHaveTextContent('MP4');
        expect(getValue('Media type')).toHaveTextContent('Video');
        expect(getValue('Total frames')).toHaveTextContent('400');
        expect(getValue('Frame rate')).toHaveTextContent('29.97 FPS');
        expect(getValue('Duration')).toHaveTextContent('00:12');
        await user.click(screen.getByRole('button', { name: 'Close' }));
        expect(onClose).toHaveBeenCalledTimes(1);
    });
});
