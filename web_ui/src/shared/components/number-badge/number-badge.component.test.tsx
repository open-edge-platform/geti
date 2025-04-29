// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { NumberBadge } from './number-badge.component';

describe('NumberBadge', () => {
    it('should show a loading UI if the jobsNumber is "null"', () => {
        render(<NumberBadge id='fake-id' jobsNumber={null} />);

        expect(screen.getByLabelText('Loading...')).toBeInTheDocument();
    });

    it('should show a loading UI if "isPending" is true', () => {
        render(<NumberBadge id='fake-id' jobsNumber={3} isPending />);

        expect(screen.getByLabelText('Loading...')).toBeInTheDocument();
    });

    it('should not render anything if jobsNumber is 0', () => {
        render(<NumberBadge id='fake-id' jobsNumber={0} />);

        expect(screen.queryByTestId('number badge')).not.toBeInTheDocument();
    });

    it('should render properly with a valid number', () => {
        render(<NumberBadge id='fake-id' jobsNumber={3} />);

        expect(screen.getByTestId('number badge')).toBeInTheDocument();
        expect(screen.getByTestId('number-badge-fake-id-value')).toBeInTheDocument();
        expect(screen.getByTestId('number-badge-fake-id-value')).toHaveTextContent('3');
    });
});
