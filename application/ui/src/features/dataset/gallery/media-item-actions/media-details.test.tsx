// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { AnnotatedVideoFrame, AnnotationDTO, Media } from '@/api/types';
import { DialogContainer } from '@geti-ui/ui';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { getMockedMediaImage, getMockedVideo } from 'mocks/mock-media';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { annotationsQueryOptions } from '../../../../modules/annotator/shell/api/use-annotations-query';
import { server } from '../../../../msw-node-setup';
import { createQueryClient } from '../../../../query-client/query-client';
import { EMPTY_LABEL_ID } from '../../../../shared/labels';
import { MediaDetails } from './media-details.component';

rs.mock('hooks/use-project-identifier.hook', () => ({ useProjectIdentifier: () => 'project-123' }));

const annotations: AnnotationDTO[] = [
    { shape: { type: 'rectangle', x: 0, y: 0, width: 20, height: 20 }, labels: [{ id: 'label-1' }] },
    { shape: { type: 'rectangle', x: 20, y: 20, width: 20, height: 20 }, labels: [{ id: 'label-1' }] },
];

const getValue = (label: string) => screen.getByText(label, { selector: 'dt' }).nextElementSibling;

const renderDetails = (
    item: Media = getMockedMediaImage({ annotation_status: { has_annotations: true } }),
    queryClient = createQueryClient()
) => {
    const onClose = rs.fn();
    render(
        <DialogContainer onDismiss={onClose}>
            <MediaDetails item={item} onClose={onClose} />
        </DialogContainer>,
        { queryClient }
    );
    return onClose;
};

describe('Media details', () => {
    it('shows resolution, file size and exact annotation counts', async () => {
        const request = rs.fn();
        server.use(
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', () => {
                request();
                return HttpResponse.json({ annotations, user_reviewed: true, subset: 'training' });
            })
        );
        const item = getMockedMediaImage({
            name: 'inspection',
            width: 1920,
            height: 1080,
            size: 1500000,
            annotation_status: { has_annotations: true },
        });
        const user = userEvent.setup();
        const onClose = renderDetails(item);

        await screen.findByRole('dialog', { name: 'Details' });
        expect(screen.queryByRole('region', { name: 'Details' })).not.toBeInTheDocument();
        await waitFor(() => expect(getValue('Annotations')).toHaveTextContent('2'));
        expect(request).toHaveBeenCalledTimes(1);
        expect(getValue('Unique labels')).toHaveTextContent('1');
        expect(getValue('Resolution')).toHaveTextContent('1920 × 1080 px');
        expect(getValue('File size')).toHaveTextContent('1.5 MB');
        expect(screen.getByRole('status')).toHaveTextContent('Annotated');
        expect(screen.queryByText('Frame rate')).not.toBeInTheDocument();
        await user.click(screen.getByRole('button', { name: 'Close' }));
        expect(onClose).toHaveBeenCalledTimes(1);
    });

    it.each([
        { item: getMockedMediaImage({ name: 'inspection.v2', format: 'jpg' }), fileName: 'inspection.v2.jpg' },
        { item: getMockedMediaImage({ name: 'inspection', format: 'jpeg' }), fileName: 'inspection.jpeg' },
        { item: getMockedMediaImage({ name: 'inspection', format: 'tiff' }), fileName: 'inspection.tiff' },
        {
            item: getMockedVideo({
                name: 'boxes',
                format: 'mp4',
                annotation_status: { has_annotations: false, annotated_video_frames: 0 },
            }),
            fileName: 'boxes.mp4',
        },
    ])('shows the download filename $fileName in the heading and tooltip', ({ item, fileName }) => {
        renderDetails(item);

        expect(screen.getByRole('heading', { name: fileName, level: 3 })).toHaveAttribute('title', fileName);
        expect(screen.getByRole('img')).toHaveAttribute(
            'src',
            expect.stringMatching(new RegExp(`/api/projects/project-123/dataset/media/${item.id}/thumbnail$`))
        );
    });

    it('counts a saved No object image as one annotation and one unique label', async () => {
        server.use(
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', () =>
                HttpResponse.json({ annotations: [], user_reviewed: true, subset: 'unassigned' })
            )
        );
        renderDetails();
        await waitFor(() => expect(getValue('Annotations')).toHaveTextContent('1'));
        expect(getValue('Unique labels')).toHaveTextContent('1');
        expect(screen.getByRole('status')).toHaveTextContent('Annotated');
    });

    it.each([
        getMockedMediaImage(),
        getMockedVideo({ annotation_status: { has_annotations: false, annotated_video_frames: 0 } }),
    ])('shows zero without requesting annotations for unannotated $type', async (item) => {
        const request = rs.fn();
        server.use(
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', () => {
                request();
                return new HttpResponse(null, { status: 500 });
            }),
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/frames', () => {
                request();
                return new HttpResponse(null, { status: 500 });
            })
        );
        renderDetails(item);
        expect(getValue('Annotations')).toHaveTextContent('0');
        expect(getValue('Unique labels')).toHaveTextContent('0');
        expect(screen.getByRole('status')).toHaveTextContent('Unannotated');
        await userEvent.click(screen.getByRole('button', { name: 'Close' }));
        expect(request).not.toHaveBeenCalled();
    });

    it('counts the No object annotation cached by the annotator for an image', async () => {
        const item = getMockedMediaImage({ annotation_status: { has_annotations: true } });
        const request = rs.fn();
        server.use(
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', () => {
                request();
                return HttpResponse.json({ annotations: [], user_reviewed: true, subset: 'unassigned' });
            })
        );
        const queryClient = createQueryClient();
        const options = annotationsQueryOptions('project-123', item);
        await queryClient.fetchQuery(options);

        renderDetails(item, queryClient);

        expect(getValue('Annotations')).toHaveTextContent('1');
        expect(getValue('Unique labels')).toHaveTextContent('1');
        expect(screen.getByRole('status')).toHaveTextContent('Annotated');
        expect(request).toHaveBeenCalledTimes(1);
    });

    it('preserves empty-label normalization when the annotator reads data fetched by Details', async () => {
        const request = rs.fn();
        server.use(
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', () => {
                request();
                return HttpResponse.json({ annotations: [], user_reviewed: true, subset: 'unassigned' });
            })
        );
        const item = getMockedMediaImage({ annotation_status: { has_annotations: true } });
        const queryClient = createQueryClient();
        renderDetails(item, queryClient);
        await waitFor(() => expect(getValue('Annotations')).toHaveTextContent('1'));

        const data = await queryClient.fetchQuery(annotationsQueryOptions('project-123', item));

        expect(data.annotations).toEqual([{ shape: { type: 'full_image' }, labels: [{ id: EMPTY_LABEL_ID }] }]);
        expect(request).toHaveBeenCalledTimes(1);
    });

    it('keeps unannotated status when the annotator has cached an empty result', () => {
        const item = getMockedMediaImage();
        const queryClient = createQueryClient();
        queryClient.setQueryData(annotationsQueryOptions('project-123', item).queryKey, {
            annotations: [],
            user_reviewed: false,
            subset: 'unassigned',
        });

        renderDetails(item, queryClient);

        expect(getValue('Annotations')).toHaveTextContent('0');
        expect(getValue('Unique labels')).toHaveTextContent('0');
        expect(screen.getByRole('status')).toHaveTextContent('Unannotated');
    });

    it('shows a loading state then permits retry without displaying a misleading zero on failure', async () => {
        server.use(
            http.get(
                '/api/projects/{project_id}/dataset/media/{media_id}/annotations',
                () => new HttpResponse(null, { status: 500 })
            )
        );
        renderDetails();
        expect(screen.getByRole('status')).toHaveTextContent('Annotated');
        expect(getValue('Annotations')).toHaveTextContent('Loading...');
        await waitFor(() => expect(getValue('Annotations')).toHaveTextContent('Unavailable'));
        expect(screen.getByRole('status')).toHaveTextContent('Annotated');
        server.use(
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', () =>
                HttpResponse.json({ annotations, user_reviewed: true, subset: 'unassigned' })
            )
        );
        await userEvent.click(screen.getByRole('button', { name: 'Retry' }));
        await waitFor(() => expect(getValue('Annotations')).toHaveTextContent('2'));
    });

    it('counts annotations across the video separately from annotated frames', async () => {
        const requestedRange = rs.fn();
        const frames: AnnotatedVideoFrame[] = [
            {
                media_id: 'frame-0',
                frame_index: 0,
                annotation_data: { annotations, user_reviewed: true, subset: 'training' },
            },
            {
                media_id: 'frame-10',
                frame_index: 10,
                annotation_data: { annotations: [], user_reviewed: true, subset: 'training' },
            },
            {
                // A distinct label on the last frame catches both truncated ranges and an off-by-one upper bound.
                media_id: 'frame-399',
                frame_index: 399,
                annotation_data: {
                    annotations: [
                        { shape: { type: 'full_image' }, labels: [{ id: 'label-2' }] },
                        { shape: { type: 'full_image' }, labels: [{ id: 'label-2' }] },
                    ],
                    user_reviewed: true,
                    subset: 'training',
                },
            },
        ];
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
        render(
            <DialogContainer onDismiss={rs.fn()}>
                <MediaDetails
                    item={getMockedVideo({
                        fps: 29.97,
                        duration: 12.5,
                        frame_count: 400,
                        annotation_status: { has_annotations: true, annotated_video_frames: 3 },
                    })}
                    onClose={rs.fn()}
                />
            </DialogContainer>
        );
        expect(getValue('Annotated frames')).toHaveTextContent('3');
        expect(getValue('Annotations')).toHaveTextContent('Loading...');
        await waitFor(() => expect(getValue('Annotations')).toHaveTextContent('5'));
        expect(getValue('Unique labels')).toHaveTextContent('3');
        expect(requestedRange).toHaveBeenCalledWith('0', '399');
        expect(getValue('Total frames')).toHaveTextContent('400');
        expect(getValue('Frame rate')).toHaveTextContent('29.97 FPS');
        expect(getValue('Duration')).toHaveTextContent('12.5 s');
    });

    it.each([
        { userReviewed: true, expectedCount: 2, expectedLabelCount: 1 },
        { userReviewed: false, expectedCount: 0, expectedLabelCount: 0 },
    ])(
        'counts empty video frames with user_reviewed=$userReviewed as $expectedCount annotations and $expectedLabelCount unique labels',
        async ({ userReviewed, expectedCount, expectedLabelCount }) => {
            server.use(
                http.get('/api/projects/{project_id}/dataset/media/{media_id}/frames', () =>
                    HttpResponse.json(
                        [0, 10].map((frameIndex) => ({
                            media_id: `frame-${frameIndex}`,
                            frame_index: frameIndex,
                            annotation_data: {
                                annotations: [],
                                user_reviewed: userReviewed,
                                subset: 'unassigned' as const,
                            },
                        }))
                    )
                )
            );
            renderDetails(getMockedVideo({ annotation_status: { has_annotations: true, annotated_video_frames: 2 } }));

            await waitFor(() => expect(getValue('Annotations')).toHaveTextContent(String(expectedCount)));
            expect(getValue('Unique labels')).toHaveTextContent(String(expectedLabelCount));
            expect(getValue('Annotated frames')).toHaveTextContent('2');
        }
    );

    it('preserves video status and annotated frame count when frame details fail to load', async () => {
        server.use(
            http.get(
                '/api/projects/{project_id}/dataset/media/{media_id}/frames',
                () => new HttpResponse(null, { status: 500 })
            )
        );
        renderDetails(getMockedVideo({ annotation_status: { has_annotations: true, annotated_video_frames: 3 } }));

        expect(getValue('Annotated frames')).toHaveTextContent('3');
        await waitFor(() => expect(getValue('Annotations')).toHaveTextContent('Unavailable'));
        expect(getValue('Unique labels')).toHaveTextContent('Unavailable');
        expect(getValue('Annotated frames')).toHaveTextContent('3');
        expect(screen.getByRole('status')).toHaveTextContent('Annotated');
        expect(screen.getByRole('button', { name: 'Retry' })).toBeVisible();
    });
});
