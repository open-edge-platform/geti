// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from 'test-utils/render';

import { SUBSET_PARAM } from '../../../../../hooks/use-dataset-filters-search-params.hook';
import { FilterBySubset } from './filter-by-subset.component';

const openSubsetFilter = async (user: ReturnType<typeof userEvent.setup>) => {
    await user.click(screen.getByRole('button', { name: 'Filter by subset' }));

    return screen.findByRole('dialog', { name: 'Filter media items' });
};

describe('FilterBySubset', () => {
    it('shows a placeholder when no subset is selected', () => {
        render(<FilterBySubset />, { route: '/projects/123', path: '/projects/:projectId' });

        expect(screen.getByText('All subsets')).toBeVisible();
    });

    it('shows a chip for each subset already selected via the search params', () => {
        render(<FilterBySubset />, {
            route: `/projects/123?${SUBSET_PARAM}=training,validation`,
            path: '/projects/:projectId',
        });

        expect(screen.getByText('Training')).toBeVisible();
        expect(screen.getByText('Validation')).toBeVisible();
        expect(screen.queryByText('All subsets')).not.toBeInTheDocument();
    });

    it('removes a subset filter chip when its close icon is clicked', async () => {
        const user = userEvent.setup();

        render(<FilterBySubset />, {
            route: `/projects/123?${SUBSET_PARAM}=training,validation`,
            path: '/projects/:projectId',
        });

        const trainingChip = screen.getByText('Training').closest('div');
        const closeIcon = trainingChip?.querySelector('svg');

        expect(closeIcon).toBeTruthy();

        await user.click(closeIcon as SVGElement);

        expect(screen.queryByText('Training')).not.toBeInTheDocument();
        expect(screen.getByText('Validation')).toBeVisible();
    });

    it('allows selecting multiple subsets from the popover', async () => {
        const user = userEvent.setup();

        render(<FilterBySubset />, { route: '/projects/123', path: '/projects/:projectId' });

        const dialog = await openSubsetFilter(user);

        await user.click(within(dialog).getByText('Training'));
        await user.click(within(dialog).getByText('Testing'));

        await waitFor(() => {
            expect(screen.getAllByText('Training').length).toBeGreaterThan(0);
        });

        expect(screen.getAllByText('Testing').length).toBeGreaterThan(0);
        expect(screen.queryByText('All subsets')).not.toBeInTheDocument();
    });

    it('selects every subset when "Toggle all" is checked', async () => {
        const user = userEvent.setup();

        render(<FilterBySubset />, { route: '/projects/123', path: '/projects/:projectId' });

        const dialog = await openSubsetFilter(user);

        await user.click(within(dialog).getByRole('checkbox', { name: 'Select all items' }));

        await waitFor(() => {
            expect(screen.getAllByText('Unassigned').length).toBeGreaterThan(0);
        });

        expect(screen.getAllByText('Training').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Validation').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Testing').length).toBeGreaterThan(0);
    });
});
