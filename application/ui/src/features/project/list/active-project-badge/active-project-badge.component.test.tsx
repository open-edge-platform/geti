// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen } from '@testing-library/react';
import { render } from 'test-utils/render';

import { ActiveProjectBadge } from './active-project-badge.component';

describe('ActiveProjectBadge', () => {
    it('renders the "Active" label', () => {
        render(<ActiveProjectBadge />);

        expect(screen.getByText('Active')).toBeInTheDocument();
    });

    it('does not apply the small-size class by default', () => {
        render(<ActiveProjectBadge />);

        const badge = screen.getByText('Active').closest('[role="presentation"]');
        expect(badge?.className).not.toMatch(/small/i);
    });

    it('applies the small-size class when size="S"', () => {
        render(<ActiveProjectBadge size='S' />);

        const badge = screen.getByText('Active').closest('[role="presentation"]');
        expect(badge?.className).toMatch(/small/i);
    });
});
