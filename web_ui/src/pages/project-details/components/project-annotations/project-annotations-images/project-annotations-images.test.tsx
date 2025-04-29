// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { act, render, screen, waitFor } from '@testing-library/react';

import { getById } from '../../../../../test-utils/utils';
import { ProjectAnnotationsImages } from './project-annotations-images.component';

describe('Project annotations images', () => {
    const annotatedImagesValue = 5;
    const imagesValue = 10;
    const gridArea = 'images';

    beforeAll(() => {
        jest.useFakeTimers();
        jest.useRealTimers();
    });

    afterAll(() => {
        jest.clearAllTimers();
    });

    it('should display images value with progress before animation', () => {
        render(
            <ProjectAnnotationsImages annotatedImages={annotatedImagesValue} images={imagesValue} gridArea={gridArea} />
        );
        const imagesTitle = screen.getByText('Annotated images');
        const imagesCount = screen.getByText('0');
        const progressCount = screen.getByText('0%');

        expect(imagesTitle).toBeInTheDocument();
        expect(imagesCount).toBeInTheDocument();
        expect(progressCount).toBeInTheDocument();
    });

    it('should display images value with progress after animation', async () => {
        const { container } = render(
            <ProjectAnnotationsImages annotatedImages={annotatedImagesValue} images={imagesValue} gridArea={gridArea} />
        );
        const imagesTitle = screen.getByText('Annotated images');
        expect(imagesTitle).toBeInTheDocument();

        // Wrapped in "act" because advancing time will trigger a useEffect on the ProgressBar component inside
        // ProjectAnnotationsImages component
        act(() => {
            // Default duration for CountUp's animation is 2 seconds
            jest.advanceTimersByTime(2000);
        });

        await waitFor(() => {
            const annotatedImagesWrapper = getById(container, 'annotated-images-count-id');
            expect(annotatedImagesWrapper).toHaveTextContent(`${annotatedImagesValue}`);

            const progressWrapper = getById(container, 'annotated-images-progress-bar-id');
            const progressCalcValue = Math.round((annotatedImagesValue / imagesValue) * 100);
            expect(progressWrapper).toHaveTextContent(`${progressCalcValue}`);
        });
    });
});
