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
import { userEvent } from '@testing-library/user-event';

import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { PlaybackSpeedSlider } from './playback-rate-slider.component';
import { useStreamingVideoPlayer } from './streaming-video-player-provider.component';

jest.mock('./streaming-video-player-provider.component', () => ({
    ...jest.requireActual('./streaming-video-player-provider.component'),
    useStreamingVideoPlayer: jest.fn(),
}));

const getPlaybackButton = () => screen.getByRole('button', { name: 'Open playback speed' });

it('Sets the playback rate to a slower value', async () => {
    const setPlaybackRate = jest.fn();
    const playbackRate = 1.0;

    // @ts-expect-error We only want to mock the playback rate
    jest.mocked(useStreamingVideoPlayer).mockReturnValue({ setPlaybackRate, playbackRate });

    render(<PlaybackSpeedSlider />);
    await userEvent.click(getPlaybackButton());

    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: 2 } });

    expect(setPlaybackRate).toHaveBeenCalledWith(0.5);

    fireEvent.change(slider, { target: { value: 1 } });

    expect(setPlaybackRate).toHaveBeenCalledWith(0.25);
});

it('Reverts the playback rate to a normal value', async () => {
    const setPlaybackRate = jest.fn();
    const playbackRate = 0.25;

    // @ts-expect-error We only want to mock the playback rate
    jest.mocked(useStreamingVideoPlayer).mockReturnValue({ setPlaybackRate, playbackRate });

    render(<PlaybackSpeedSlider />);
    await userEvent.click(getPlaybackButton());

    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: 2 } });

    expect(setPlaybackRate).toHaveBeenCalledWith(0.5);

    fireEvent.change(slider, { target: { value: 3 } });

    expect(setPlaybackRate).toHaveBeenCalledWith(1);
});
