// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
