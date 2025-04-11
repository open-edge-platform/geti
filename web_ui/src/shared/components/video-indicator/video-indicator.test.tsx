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
