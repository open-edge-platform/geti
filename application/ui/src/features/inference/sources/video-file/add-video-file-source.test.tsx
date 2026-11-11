// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import * as actualTus from '../../../../api/tus-upload' with { rstest: 'importActual' };
import { transferFile } from '../../../../api/tus-upload';
import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { AddVideoFileSource } from './add-video-file-source.component';

rs.mock('../../../../api/tus-upload', () => ({
    ...actualTus,
    transferFile: rs.fn(),
}));

const mediaId = '712750b2-5a82-47ee-8fba-f3dc96cb615d';
const uploadedPath = `/data/source_media/${mediaId}/sample.mp4`;

const setup = ({ createStatus = 200 } = {}) => {
    let currentCreateStatus = createStatus;
    const uploadSpy = rs.fn();
    const createSpy = rs.fn();
    const deleteSpy = rs.fn();
    const pipelineSpy = rs.fn();
    const onSaved = rs.fn();

    rs.mocked(transferFile).mockResolvedValue('00000000-0000-4000-8000-000000000001');

    server.use(
        http.post('/api/sources/media:from-upload', () => {
            uploadSpy();

            return HttpResponse.json({ video_path: uploadedPath }, { status: 201 });
        }),
        http.delete('/api/sources/media/{source_media_id}', ({ params }) => {
            deleteSpy(params.source_media_id);

            return HttpResponse.json({ deleted_video_path: uploadedPath });
        }),
        http.post('/api/sources', async ({ request }) => {
            const body = await request.json();
            createSpy(body);

            return currentCreateStatus === 200
                ? HttpResponse.json({ ...body, id: 'new-id' } as never)
                : HttpResponse.json({ detail: 'boom' } as never, { status: currentCreateStatus as 500 });
        }),
        http.post('/api/sources/{source_id}:test', () => HttpResponse.json({ reachable: true })),
        http.patch('/api/projects/{project_id}/pipeline', async ({ request }) => {
            pipelineSpy(await request.json());

            return HttpResponse.json({ project_id: '123', status: 'idle', device: 'cpu' });
        })
    );

    render(<AddVideoFileSource existingNames={[]} onSaved={onSaved} />);

    return {
        uploadSpy,
        createSpy,
        deleteSpy,
        pipelineSpy,
        onSaved,
        setCreateStatus: (status: number) => (currentCreateStatus = status),
    };
};

const selectFile = async () => {
    await userEvent.upload(
        screen.getByTestId('upload-video-file'),
        new File(['fake-video-bytes'], 'sample.mp4', { type: 'video/mp4' })
    );
};

const submit = () => userEvent.click(screen.getByRole('button', { name: 'Add & Use' }));

describe('AddVideoFileSource', () => {
    beforeEach(() => {
        rs.clearAllMocks();
    });

    it('uploads the selected file, creates the source with the uploaded path (no id) and connects it', async () => {
        const { uploadSpy, createSpy, pipelineSpy, onSaved } = setup();

        await selectFile();
        await submit();

        await waitFor(() => expect(onSaved).toHaveBeenCalledOnce());
        expect(uploadSpy).toHaveBeenCalledOnce();
        expect(createSpy).toHaveBeenCalledWith({
            name: 'Video file source',
            source_type: 'video_file',
            video_path: uploadedPath,
            loop: false,
        });
        expect(pipelineSpy).toHaveBeenCalledWith({ source_id: 'new-id' });
    });

    it('does not upload when a path is typed', async () => {
        const { uploadSpy, createSpy, onSaved } = setup();

        await userEvent.type(screen.getByRole('textbox', { name: /Video file path/ }), '/a/b.mp4');
        await userEvent.click(screen.getByRole('switch', { name: 'loop video' }));
        await submit();

        await waitFor(() => expect(onSaved).toHaveBeenCalledOnce());
        expect(uploadSpy).not.toHaveBeenCalled();
        expect(createSpy).toHaveBeenCalledWith({
            name: 'Video file source',
            source_type: 'video_file',
            video_path: '/a/b.mp4',
            loop: true,
        });
    });

    it('disables "Add & Use" and does not submit without a path or a file', async () => {
        const { uploadSpy, createSpy } = setup();

        expect(screen.getByRole('button', { name: 'Add & Use' })).toBeDisabled();
        await userEvent.click(screen.getByRole('button', { name: 'Add & Use' }));

        expect(createSpy).not.toHaveBeenCalled();
        expect(uploadSpy).not.toHaveBeenCalled();
    });

    it('deletes the uploaded video when the source cannot be created', async () => {
        const { deleteSpy, pipelineSpy, onSaved } = setup({ createStatus: 500 });

        await selectFile();
        await submit();

        await waitFor(() => expect(deleteSpy).toHaveBeenCalledWith(mediaId));
        expect(await screen.findByText('Failed to save source configuration, boom')).toBeVisible();
        expect(deleteSpy).toHaveBeenCalledTimes(1);
        expect(screen.getByRole('button', { name: 'Add & Use' })).toBeVisible();
        expect(pipelineSpy).not.toHaveBeenCalled();
        expect(onSaved).not.toHaveBeenCalled();
    });

    it('keeps the selected file after a failed save and uploads it again on retry', async () => {
        const { uploadSpy, createSpy, pipelineSpy, onSaved, setCreateStatus } = setup({ createStatus: 500 });

        await selectFile();
        await submit();

        await waitFor(() => expect(createSpy).toHaveBeenCalledTimes(1));
        expect(await screen.findByText('Failed to save source configuration, boom')).toBeVisible();
        expect(screen.getByText('Selected: sample.mp4')).toBeVisible();
        expect(onSaved).not.toHaveBeenCalled();

        setCreateStatus(200);
        await submit();

        await waitFor(() => expect(onSaved).toHaveBeenCalledOnce());
        expect(uploadSpy).toHaveBeenCalledTimes(2);
        expect(createSpy).toHaveBeenCalledTimes(2);
        expect(createSpy).toHaveBeenLastCalledWith({
            name: 'Video file source',
            source_type: 'video_file',
            video_path: uploadedPath,
            loop: false,
        });
        expect(pipelineSpy).toHaveBeenCalledWith({ source_id: 'new-id' });
    });

    it('creates no source and shows no error toast when the upload is cancelled', async () => {
        const { createSpy, onSaved } = setup();
        rs.mocked(transferFile).mockImplementation(
            async (_file, options) =>
                new Promise((_resolve, reject) => {
                    options?.onProgress?.(1);
                    options?.signal?.addEventListener('abort', () => reject(actualTus.createAbortError()));
                })
        );

        await selectFile();
        await submit();
        await userEvent.click(await screen.findByRole('button', { name: 'Cancel' }));

        await waitFor(() => expect(screen.queryByRole('progressbar')).not.toBeInTheDocument());
        expect(createSpy).not.toHaveBeenCalled();
        expect(onSaved).not.toHaveBeenCalled();
        expect(screen.queryByText(/cancelled/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/Failed to save/)).not.toBeInTheDocument();
        expect(screen.getByText('Selected: sample.mp4')).toBeVisible();
    });
});
