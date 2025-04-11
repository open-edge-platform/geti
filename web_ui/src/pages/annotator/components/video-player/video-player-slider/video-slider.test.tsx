// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
