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

import { render, screen, waitFor } from '@testing-library/react';

import { getById } from '../../../../../test-utils/utils';
import { ProjectAnnotationsVideos } from './project-annotations-videos.component';

describe('Project annotations videos', () => {
    const annotatedVideos = 10;
    const annotatedFrames = 7;
    const gridArea = 'videos';

    beforeAll(() => {
        jest.useFakeTimers();
    });

    afterAll(() => {
        jest.useRealTimers();
        jest.clearAllTimers();
    });

    it('should display videos and frames values before animation', () => {
        const { container } = render(
            <ProjectAnnotationsVideos
                annotatedVideos={annotatedVideos}
                annotatedFrames={annotatedFrames}
                gridArea={gridArea}
            />
        );

        const annotatedVideosFrames = screen.getByText('Annotated videos / frames');
        expect(annotatedVideosFrames).toBeInTheDocument();

        const videosTitle = screen.getByText('Videos:');
        const framesTitle = screen.getByText('Frames:');
        expect(videosTitle).toBeInTheDocument();
        expect(framesTitle).toBeInTheDocument();

        const videosWrapper = getById(container, 'annotated-videos-count-id');
        const framesWrapper = getById(container, 'annotated-frame-count-id');
        expect(videosWrapper).toHaveTextContent('0');
        expect(framesWrapper).toHaveTextContent('0');
    });

    it('should display videos and frames after animation', async () => {
        const { container } = render(
            <ProjectAnnotationsVideos
                annotatedVideos={annotatedVideos}
                annotatedFrames={annotatedFrames}
                gridArea={gridArea}
            />
        );

        // Default duration for CountUp's animation is 2 seconds
        jest.advanceTimersByTime(2000);

        await waitFor(() => {
            const videosWrapper = getById(container, 'annotated-videos-count-id');
            const framesWrapper = getById(container, 'annotated-frame-count-id');

            expect(videosWrapper).toHaveTextContent(`${annotatedVideos}`);
            expect(framesWrapper).toHaveTextContent(`${annotatedFrames}`);
        });
    });
});
