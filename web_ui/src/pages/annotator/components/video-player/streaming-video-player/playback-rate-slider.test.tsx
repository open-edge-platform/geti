// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
