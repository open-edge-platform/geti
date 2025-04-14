// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { Tag } from './tag.component';

describe('Tag', () => {
    it('render with a dot by default', () => {
        render(<Tag text='test tag' id='test-id' />);

        expect(screen.getByTestId('test-id').children).toHaveLength(2);
    });

    it('render without a dot correctly', () => {
        render(<Tag text='test tag' withDot={false} id='test-id' />);

        expect(screen.getByTestId('test-id').children).toHaveLength(1);
    });

    it('render with a prefix if provided', () => {
        render(<Tag text='test tag' prefix={<div>Fake icon</div>} />);

        expect(screen.getByText('Fake icon')).toBeInTheDocument();
    });

    it('render with a suffix if provided', () => {
        render(<Tag text='test tag' suffix={<div>Fake icon</div>} />);

        expect(screen.getByText('Fake icon')).toBeInTheDocument();
    });
});
