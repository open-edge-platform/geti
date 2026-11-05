// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { VideoFileSourceConfig } from '@/api/types';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import * as actualTus from '../../../../api/tus-upload' with { rstest: 'importActual' };
import { transferFile } from '../../../../api/tus-upload';
import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { EditVideoFileSource } from './edit-video-file-source.component';

rs.mock('../../../../api/tus-upload', () => ({
    ...actualTus,
    transferFile: rs.fn(),
}));

const mediaId = '712750b2-5a82-47ee-8fba-f3dc96cb615d';
const uploadedPath = `/data/source_media/${mediaId}/sample.mp4`;

const source: VideoFileSourceConfig = {
    id: 'video-id',
    name: 'My video',
    source_type: 'video_file',
    video_path: '/old/path.mp4',
    loop: false,
};

const setup = ({ isConnected = false, updateStatus = 200 } = {}) => {
    const uploadSpy = rs.fn();
    const updateSpy = rs.fn();
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
        http.patch('/api/sources/{source_id}', async ({ request }) => {
            updateSpy(await request.json());

            return updateStatus === 200
                ? HttpResponse.json(source)
                : HttpResponse.json({ detail: 'boom' } as never, { status: updateStatus as 500 });
        }),
        http.post('/api/sources/{source_id}:test', () => HttpResponse.json({ reachable: true })),
        http.patch('/api/projects/{project_id}/pipeline', async ({ request }) => {
            pipelineSpy(await request.json());

            return HttpResponse.json({ project_id: '123', status: 'idle', device: 'cpu' });
        })
    );

    render(<EditVideoFileSource source={source} isConnected={isConnected} onSaved={onSaved} onBackToList={rs.fn()} />);

    return { uploadSpy, updateSpy, deleteSpy, pipelineSpy, onSaved };
};

const selectFile = async () => {
    await userEvent.upload(
        screen.getByTestId('upload-video-file'),
        new File(['fake-video-bytes'], 'sample.mp4', { type: 'video/mp4' })
    );
};

describe('EditVideoFileSource', () => {
    beforeEach(() => {
        rs.clearAllMocks();
    });

    it('patches without id and source_type, without uploading, and does not connect on Save', async () => {
        const { uploadSpy, updateSpy, pipelineSpy, onSaved } = setup();

        const name = screen.getByRole('textbox', { name: 'Name' });
        await userEvent.clear(name);
        await userEvent.type(name, 'Renamed');
        await userEvent.click(screen.getByRole('button', { name: 'Save' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledOnce());
        expect(updateSpy).toHaveBeenCalledWith({ name: 'Renamed', video_path: '/old/path.mp4', loop: false });
        expect(uploadSpy).not.toHaveBeenCalled();
        expect(pipelineSpy).not.toHaveBeenCalled();
    });

    it('uploads the selected file and patches with the new path', async () => {
        const { uploadSpy, updateSpy, onSaved } = setup();

        await selectFile();
        await userEvent.click(screen.getByRole('button', { name: 'Save' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledOnce());
        expect(uploadSpy).toHaveBeenCalledOnce();
        expect(updateSpy).toHaveBeenCalledWith({ name: 'My video', video_path: uploadedPath, loop: false });
    });

    it('deletes the uploaded video when the source cannot be updated and keeps the file for a retry', async () => {
        const { deleteSpy, onSaved } = setup({ updateStatus: 500 });

        await selectFile();
        await userEvent.click(screen.getByRole('button', { name: 'Save' }));

        await waitFor(() => expect(deleteSpy).toHaveBeenCalledWith(mediaId));
        expect(await screen.findByText('Failed to save source configuration, boom')).toBeVisible();
        expect(screen.getByText('Selected: sample.mp4')).toBeVisible();
        expect(onSaved).not.toHaveBeenCalled();
    });

    it('connects the source to the pipeline only on "Save & Connect"', async () => {
        const { pipelineSpy, onSaved } = setup();

        await userEvent.type(screen.getByRole('textbox', { name: 'Name' }), '!');
        await userEvent.click(screen.getByRole('button', { name: 'Save & Connect' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledOnce());
        expect(pipelineSpy).toHaveBeenCalledWith({ source_id: 'video-id' });
    });

    it('disables "Save" and "Save & Connect" until a value changes or a file is selected', async () => {
        setup();

        expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
        expect(screen.getByRole('button', { name: 'Save & Connect' })).toBeDisabled();

        await selectFile();

        expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled();
        expect(screen.getByRole('button', { name: 'Save & Connect' })).toBeEnabled();
    });

    it('hides "Save & Connect" when the source is connected', () => {
        setup({ isConnected: true });

        expect(screen.getByRole('button', { name: 'Save' })).toBeVisible();
        expect(screen.queryByRole('button', { name: 'Save & Connect' })).not.toBeInTheDocument();
    });
});
