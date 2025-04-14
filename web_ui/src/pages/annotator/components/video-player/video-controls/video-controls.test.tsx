// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { annotatorRender as render } from '../../../test-utils/annotator-render';
import { getMockedVideoControls } from './test-utils';
import { Controls as VideoControls } from './video-controls.component';

describe('Video controls', () => {
    const videoControls = getMockedVideoControls({});

    it('Goes to the previous frame', async () => {
        await render(<VideoControls videoControls={videoControls} />);

        fireEvent.click(await screen.findByRole('button', { name: /Go to previous frame/ }));
        expect(videoControls.previous).toHaveBeenCalled();
    });

    it('Goes to the next frame', async () => {
        await render(<VideoControls videoControls={videoControls} />);

        fireEvent.click(await screen.findByRole('button', { name: /Go to next frame/ }));
        expect(videoControls.next).toHaveBeenCalled();
    });

    it('Plays the video', async () => {
        await render(<VideoControls videoControls={videoControls} />);

        fireEvent.click(await screen.findByRole('button', { name: /Play video/ }));
        expect(videoControls.play).toHaveBeenCalled();
    });

    it('Pauses the video', async () => {
        await render(<VideoControls videoControls={{ ...videoControls, isPlaying: true }} />);

        fireEvent.click(await screen.findByRole('button', { name: /Pause video/ }));
        expect(videoControls.pause).toHaveBeenCalled();
    });
});
