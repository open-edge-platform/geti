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
import { ProjectAnnotationsMedia } from './project-annotations-media.component';

describe('Project annotations media', () => {
    const imagesValue = 5;
    const videosValue = 10;
    const gridArea = 'media';

    beforeAll(() => {
        jest.useFakeTimers();
    });

    afterAll(() => {
        jest.useRealTimers();
        jest.clearAllTimers();
    });

    it('should display media values with 0, before animation', () => {
        const { container } = render(
            <ProjectAnnotationsMedia images={imagesValue} videos={videosValue} gridArea={gridArea} />
        );

        const mediaTitle = screen.getByText('Number of media');
        const imagesContainer = screen.getByText('Images');
        const videosContainer = screen.getByText('Videos');
        expect(mediaTitle).toBeInTheDocument();
        expect(imagesContainer).toBeInTheDocument();
        expect(videosContainer).toBeInTheDocument();

        const imagesWrapper = getById(container, 'media-images-count-id');
        const videosWrapper = getById(container, 'media-videos-count-id');
        expect(imagesWrapper).toHaveTextContent('0');
        expect(videosWrapper).toHaveTextContent('0');
    });

    it('should display media values with provided values', async () => {
        const { container } = render(
            <ProjectAnnotationsMedia images={imagesValue} videos={videosValue} gridArea={gridArea} />
        );

        // Default duration for CountUp's animation is 2 seconds
        jest.advanceTimersByTime(2000);

        await waitFor(() => {
            const imagesWrapper = getById(container, 'media-images-count-id');
            const videosWrapper = getById(container, 'media-videos-count-id');

            expect(imagesWrapper).toHaveTextContent(`${imagesValue}`);
            expect(videosWrapper).toHaveTextContent(`${videosValue}`);
        });
    });
});
