// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { projectRender } from '../../../../../test-utils/project-provider-render';
import { VideoSlider } from './video-slider.component';

describe('Video slider', () => {
    it('Render highlightFrames frames dots', async () => {
        const highlightFrames = [10, 50, 90];
        await projectRender(
            <VideoSlider
                id='video-test'
                minValue={0}
                maxValue={100}
                lastFrame={100}
                aria-label='Videoframe'
                highlightedFrames={highlightFrames}
                buffers={[]}
            />
        );

        highlightFrames.forEach((frame) => expect(screen.queryByLabelText(`highlight-frame-${frame}`)).toBeVisible());
    });

    it('Highlights for which range of video frames we have loaded annotations', async () => {
        const highlightFrames = [10, 50, 90];
        await projectRender(
            <VideoSlider
                id='video-test'
                minValue={0}
                maxValue={100}
                lastFrame={100}
                aria-label='Videoframe'
                highlightedFrames={highlightFrames}
                buffers={[
                    { startFrame: 0, endFrame: 300, status: 'success' },
                    { startFrame: 301, endFrame: 600, status: 'loading' },
                ]}
            />
        );

        expect(screen.getByLabelText('Finished loading predictions for frames 0 to 300')).toBeVisible();
        expect(screen.getByLabelText('Loading predictions for frames 301 to 600')).toBeVisible();
    });
});
