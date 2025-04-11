// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
