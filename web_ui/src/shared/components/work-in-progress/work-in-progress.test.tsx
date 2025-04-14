// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { WorkInProgress } from './work-in-progress.component';

describe('WorkInProgress', () => {
    it('renders correctly without description', () => {
        render(<WorkInProgress />);

        expect(screen.getByText('We are working hard to get this up and running')).toBeInTheDocument();
    });

    it('renders correctly with description', () => {
        render(<WorkInProgress description='Some description' />);

        expect(screen.queryByText('We are working hard to get this up and running')).not.toBeInTheDocument();
        expect(screen.getByText('Some description')).toBeInTheDocument();
    });
});
