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

import { screen } from '@testing-library/react';

import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { getById } from '../../../../../test-utils/utils';
import { TrainingDetails, TrainingProgress } from './training-progress.component';

jest.mock('../../../../../shared/utils', () => ({
    ...jest.requireActual('../../../../../shared/utils'),
    trimText: jest.fn((text) => text),
}));

describe('training progress', () => {
    it('check if all training details are on the screen', () => {
        const training: TrainingDetails = {
            message: 'This is test message',
            progress: 68,
        };

        const { container } = render(<TrainingProgress training={training} />);

        expect(screen.getByText('This is test message')).toBeInTheDocument();
        expect(getById(container, 'training-progress-percentage')).toHaveTextContent('68%');
        expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuetext', '68%');
    });

    it('check training details when timeRemaining is undefined', () => {
        const training: TrainingDetails = {
            message: 'This is test message',
            progress: 68,
        };
        const { container } = render(<TrainingProgress training={training} />);

        const timeRemaining = getById(container, 'training-progress-time-remaining');
        const message = getById(container, 'training-progress-message');
        const progress = getById(container, 'training-progress-percentage');

        expect(timeRemaining).not.toBeInTheDocument();
        expect(message).toHaveTextContent('This is test message');
        expect(progress).toHaveTextContent('68%');
        expect(screen.queryByAltText('time remaining')).not.toBeInTheDocument();
    });

    it('check training details when progress is empty', () => {
        const training: TrainingDetails = {
            message: 'Some message',
            progress: 0,
        };
        const { container } = render(<TrainingProgress training={training} />);

        const timeRemaining = getById(container, 'training-progress-time-remaining');
        const message = getById(container, 'training-progress-message');

        expect(timeRemaining).not.toBeInTheDocument();
        expect(message).toHaveTextContent('Some message');
        expect(screen.queryByAltText('time remaining')).not.toBeInTheDocument();
    });
});
