// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { AccuracyContainer } from './accuracy-container.component';

describe('Accuracy container', () => {
    it('should show "N/A" if value is null', () => {
        render(<AccuracyContainer value={null} heading='Accuracy' />);

        expect(screen.getByText('Accuracy is not available')).toBeInTheDocument();
    });

    it('should show score value properly rounded', () => {
        render(<AccuracyContainer value={0.76} heading='Accuracy' />);

        expect(screen.getByLabelText(/accuracy value/i)).toHaveTextContent('76%');
    });
});
