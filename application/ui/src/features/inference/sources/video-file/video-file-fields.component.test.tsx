// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState, type FormEvent } from 'react';

import { Form } from '@geti-ui/ui';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from 'test-utils/render';

import type { VideoFileUploadProgress } from './api/use-upload-video-file.hook';
import type { VideoFileFormState } from './utils';
import { VideoFileFields } from './video-file-fields.component';

const initialValue: VideoFileFormState = {
    name: 'My source',
    source_type: 'video_file',
    video_path: '',
    loop: false,
};

interface RenderOptions {
    value?: VideoFileFormState;
    uploadProgress?: VideoFileUploadProgress | null;
    onCancelUpload?: () => void;
}

const renderApp = ({ value = initialValue, uploadProgress = null, onCancelUpload = rs.fn() }: RenderOptions = {}) => {
    const handleSubmit = rs.fn((event: FormEvent) => event.preventDefault());
    const onChange = rs.fn();

    const Wrapper = () => {
        const [state, setState] = useState(value);
        const [file, setFile] = useState<File | null>(null);

        return (
            <Form validationBehavior='native' onSubmit={handleSubmit}>
                <VideoFileFields
                    value={state}
                    onChange={(next) => {
                        onChange(next);
                        setState(next);
                    }}
                    file={file}
                    onFileChange={setFile}
                    uploadProgress={uploadProgress}
                    onCancelUpload={onCancelUpload}
                />
                <button type='submit'>Submit</button>
            </Form>
        );
    };

    render(<Wrapper />);

    return { handleSubmit, onChange };
};

const selectFile = async (name = 'sample.mp4') => {
    await userEvent.upload(
        screen.getByTestId('upload-video-file'),
        new File(['fake-video-bytes'], name, { type: 'video/mp4' })
    );
};

const getPathField = () => screen.getByRole('textbox', { name: /Video file path/ });

describe('VideoFileFields', () => {
    it('renders name, path and loop from the value', () => {
        renderApp({ value: { ...initialValue, video_path: '/a/b.mp4', loop: true } });

        expect(screen.getByRole('textbox', { name: 'Name' })).toHaveValue('My source');
        expect(getPathField()).toHaveValue('/a/b.mp4');
        expect(screen.getByRole('switch', { name: 'loop video' })).toBeChecked();
    });

    it('reports edits of the name and the loop switch', async () => {
        const { onChange } = renderApp();

        await userEvent.type(screen.getByRole('textbox', { name: 'Name' }), '!');
        expect(onChange).toHaveBeenLastCalledWith({ ...initialValue, name: 'My source!' });

        await userEvent.click(screen.getByRole('switch', { name: 'loop video' }));
        expect(onChange).toHaveBeenLastCalledWith({ ...initialValue, name: 'My source!', loop: true });
    });

    it('requires a path until a file is selected', async () => {
        const { handleSubmit } = renderApp();

        expect((getPathField() as HTMLInputElement).checkValidity()).toBe(false);

        await selectFile();

        expect((getPathField() as HTMLInputElement).checkValidity()).toBe(true);
        await userEvent.click(screen.getByRole('button', { name: 'Submit' }));
        expect(handleSubmit).toHaveBeenCalled();
    });

    it('selecting a file shows its name and clears the typed path', async () => {
        renderApp({ value: { ...initialValue, video_path: '/a/b.mp4' } });

        await selectFile();

        expect(screen.getByText('Selected: sample.mp4')).toBeVisible();
        expect(getPathField()).toHaveValue('');
    });

    it('typing a path drops the selected file', async () => {
        renderApp();

        await selectFile();
        await userEvent.type(getPathField(), '/a/b.mp4');

        expect(screen.queryByText('Selected: sample.mp4')).not.toBeInTheDocument();
        expect(getPathField()).toHaveValue('/a/b.mp4');
    });

    it('shows the transfer progress and lets the user cancel it', async () => {
        const onCancelUpload = rs.fn();
        renderApp({ uploadProgress: { bytesSent: 500, bytesTotal: 2000 }, onCancelUpload });

        expect(screen.getByRole('progressbar', { name: 'Upload progress' })).toHaveAttribute('aria-valuenow', '25');

        await userEvent.click(screen.getByRole('button', { name: 'Cancel' }));

        expect(onCancelUpload).toHaveBeenCalledOnce();
    });

    it('does not show progress when no transfer is running', () => {
        renderApp({ uploadProgress: null });

        expect(screen.queryByRole('progressbar')).toBeNull();
    });

    it('hides the cancel button once the transfer has completed', () => {
        renderApp({ uploadProgress: { bytesSent: 2000, bytesTotal: 2000 } });

        expect(screen.getByRole('progressbar', { name: 'Upload progress' })).toHaveAttribute('aria-valuenow', '100');
        expect(screen.queryByRole('button', { name: 'Cancel' })).toBeNull();
    });
});
