// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, render, screen } from '@testing-library/react';

import { getMockedVideoFrameMediaItem } from '../../../../../test-utils/mocked-items-factory/mocked-media';
import { VideoTimelineSlider } from './video-timeline-slider.component';

describe('VideoTimelineSlider', () => {
    const videoFrame = getMockedVideoFrameMediaItem({});
    it('navigates the video', () => {
        const sliderValue = 0;
        const setSliderValue = jest.fn();
        const handleSliderChangeEnd = jest.fn();

        render(
            <VideoTimelineSlider
                onSliderValueChangeEnd={handleSliderChangeEnd}
                onSliderValueChange={setSliderValue}
                sliderValue={sliderValue}
                videoFrame={videoFrame}
            />
        );

        const slider = screen.getByRole('slider', { name: 'Seek in video' });
        expect(slider).toHaveValue(`${videoFrame.identifier.frameNumber}`);

        fireEvent.keyDown(slider, { key: 'Right' });
        expect(setSliderValue).toHaveBeenCalledWith(1);
        expect(handleSliderChangeEnd).toHaveBeenCalledWith(1);
    });
});
