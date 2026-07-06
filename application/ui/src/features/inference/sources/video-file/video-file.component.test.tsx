// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FormEvent } from 'react';

import { Form } from '@geti-ui/ui';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { VideoFile } from './video-file.component';

describe('VideoFile', () => {
    const renderApp = (props: Parameters<typeof VideoFile>[0] = {}) => {
        const handleSubmit = vi.fn((event: FormEvent) => event.preventDefault());

        render(
            <Form validationBehavior='native' onSubmit={handleSubmit}>
                <VideoFile {...props} />
                <button type='submit'>Submit</button>
            </Form>
        );

        return { handleSubmit };
    };

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders the path input pre-filled from defaultState', () => {
        renderApp({
            defaultState: {
                id: '1',
                name: 'My source',
                source_type: 'video_file',
                video_path: '/a/b.mp4',
                loop: false,
            },
        });

        expect(screen.getByRole('textbox', { name: /Video file path/ })).toHaveValue('/a/b.mp4');
    });

    it('allows typing a path directly into the input', async () => {
        renderApp();

        const pathField = screen.getByRole('textbox', { name: /Video file path/ });
        await userEvent.type(pathField, '/a/b.mp4');

        expect(pathField).toHaveValue('/a/b.mp4');
    });

    it('marks the form invalid until a path is set', () => {
        renderApp();

        const pathField = screen.getByRole('textbox', { name: /Video file path/ }) as HTMLInputElement;
        expect(pathField.checkValidity()).toBe(false);
    });

    it('uploads a file, prefills the path input, and allows submission afterwards', async () => {
        const resolvedPath = '/data/source_media/uuid/sample.mp4';
        server.use(
            http.post('/api/sources/media', () => {
                return HttpResponse.json({ video_path: resolvedPath }, { status: 201 });
            })
        );

        const { handleSubmit } = renderApp();

        const file = new File(['fake-video-bytes'], 'sample.mp4', { type: 'video/mp4' });
        const fileInput = screen.getByTestId('upload-video-file');
        await userEvent.upload(fileInput, file);

        const pathField = screen.getByRole('textbox', { name: /Video file path/ }) as HTMLInputElement;
        await waitFor(() => {
            expect(pathField).toHaveValue(resolvedPath);
        });

        expect(screen.getByText('Uploaded')).toBeVisible();
        expect(pathField.checkValidity()).toBe(true);

        await userEvent.click(screen.getByRole('button', { name: 'Submit' }));

        expect(handleSubmit).toHaveBeenCalled();
    });

    it('shows an inline error when the upload fails', async () => {
        server.use(
            http.post('/api/sources/media', () => {
                // The 422 response has no documented schema in the OpenAPI spec (description only).
                // @ts-expect-error There is an incorrect type in OpenAPI
                return HttpResponse.json({ detail: 'Unsupported video format' }, { status: 422 });
            })
        );

        renderApp();

        const file = new File(['fake-video-bytes'], 'sample.mp4', { type: 'video/mp4' });
        const fileInput = screen.getByTestId('upload-video-file');
        await userEvent.upload(fileInput, file);

        await waitFor(() => {
            expect(screen.getByText(/upload failed: unsupported video format/i)).toBeVisible();
        });
    });
});
