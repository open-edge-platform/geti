// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { JobsIconWithNumber } from './jobs-icon-with-number.component';

describe('jobs icon with number component', () => {
    it('check if number of running jobs is properly shown', () => {
        render(<JobsIconWithNumber runningJobs={7} />);
        expect(screen.getByText('7')).toBeInTheDocument();
    });

    it('Check if there is icon displayed', () => {
        render(<JobsIconWithNumber runningJobs={7} />);
        expect(screen.getByLabelText('tasks in progress')).toBeInTheDocument();
    });
});
