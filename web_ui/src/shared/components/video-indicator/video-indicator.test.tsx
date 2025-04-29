// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { providersRender as render } from '../../../test-utils/required-providers-render';
import { VideoIndicator } from './video-indicator.component';

describe('VideoIndicator', () => {
    it('Frame and duration indicator is visible', async () => {
        render(<VideoIndicator duration={3600} frames={4} />);

        expect(screen.getByTestId('video-indicator-frames-id')).toBeInTheDocument();
        const durationIndicator = screen.getByTestId('video-indicator-duration-id');
        expect(durationIndicator).toBeInTheDocument();
        expect(durationIndicator).toHaveTextContent('01:00:00');
    });

    it('Only duration indicator is visible', async () => {
        render(<VideoIndicator duration={600} frames={undefined} />);

        expect(screen.queryByTestId('video-indicator-frames-id')).not.toBeInTheDocument();
        const durationIndicator = screen.getByTestId('video-indicator-duration-id');
        expect(durationIndicator).toBeInTheDocument();
        expect(durationIndicator).toHaveTextContent('00:10:00');
    });
});
