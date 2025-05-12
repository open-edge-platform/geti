// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { Button } from './button.component';

test('Button', () => {
    render(<Button>Test</Button>);

    expect(screen.getByRole('button', { name: 'Test' })).toBeInTheDocument();
});
