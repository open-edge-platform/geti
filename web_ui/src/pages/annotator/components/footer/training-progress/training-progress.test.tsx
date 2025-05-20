// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitFor } from '@testing-library/react';

import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { getById } from '../../../../../test-utils/utils';
import { TrainingDetails, TrainingProgress } from './training-progress.component';

jest.mock('../../../../../shared/utils', () => ({
    ...jest.requireActual('../../../../../shared/utils'),
    trimText: jest.fn((text) => text),
}));

describe('training progress', () => {
    it('check if all training details are on the screen', async () => {
        const training: TrainingDetails = {
            message: 'This is test message',
            progress: 68,
        };

        const { container } = render(<TrainingProgress training={training} />);

        await waitFor(() => {
            expect(screen.getByText('This is test message')).toBeInTheDocument();
            expect(getById(container, 'training-progress-percentage')).toHaveTextContent('68%');
            expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuetext', '68%');
        });
    });

    it('check training details when timeRemaining is undefined', async () => {
        const training: TrainingDetails = {
            message: 'This is test message',
            progress: 68,
        };
        const { container } = render(<TrainingProgress training={training} />);

        const timeRemaining = getById(container, 'training-progress-time-remaining');
        const message = getById(container, 'training-progress-message');
        const progress = getById(container, 'training-progress-percentage');

        await waitFor(() => {
            expect(timeRemaining).not.toBeInTheDocument();
            expect(message).toHaveTextContent('This is test message');
            expect(progress).toHaveTextContent('68%');
            expect(screen.queryByAltText('time remaining')).not.toBeInTheDocument();
        });
    });

    it('check training details when progress is empty', async () => {
        const training: TrainingDetails = {
            message: 'Some message',
            progress: 0,
        };
        const { container } = render(<TrainingProgress training={training} />);

        const timeRemaining = getById(container, 'training-progress-time-remaining');
        const message = getById(container, 'training-progress-message');

        await waitFor(() => {
            expect(timeRemaining).not.toBeInTheDocument();
            expect(message).toHaveTextContent('Some message');
            expect(screen.queryByAltText('time remaining')).not.toBeInTheDocument();
        });
    });
});
