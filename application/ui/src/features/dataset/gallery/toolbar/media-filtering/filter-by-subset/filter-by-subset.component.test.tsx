// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from 'test-utils/render';

import { SUBSET_PARAM } from '../../../../../../hooks/use-dataset-filters-search-params.hook';
import { FilterBySubset } from './filter-by-subset.component';

const openSubsetFilter = async (user: ReturnType<typeof userEvent.setup>) => {
    await user.click(screen.getByRole('button', { name: 'Filter by subset' }));

    return screen.findByRole('dialog', { name: 'Filter by subset' });
};

describe('FilterBySubset', () => {
    it('shows a placeholder when no subset is selected', () => {
        render(<FilterBySubset />, { route: '/projects/123', path: '/projects/:projectId' });

        expect(screen.getByText('Filter by subset')).toBeVisible();
    });

    it('shows a summary of the selected subsets from the search params', () => {
        render(<FilterBySubset />, {
            route: `/projects/123?${SUBSET_PARAM}=training,validation`,
            path: '/projects/:projectId',
        });

        expect(screen.getByText('2 subsets selected')).toBeVisible();
        expect(screen.queryByText('Filter by subset')).not.toBeInTheDocument();
    });

    it('allows selecting multiple subsets from the popover', async () => {
        const user = userEvent.setup();

        render(<FilterBySubset />, { route: '/projects/123', path: '/projects/:projectId' });

        const dialog = await openSubsetFilter(user);

        await user.click(within(dialog).getByText('Training subset'));
        await user.click(within(dialog).getByText('Testing subset'));

        await waitFor(() => {
            expect(screen.getByText('2 subsets selected')).toBeVisible();
        });

        expect(screen.queryByText('Filter by subset')).not.toBeInTheDocument();
    });

    it('selects every subset when "All subsets" is checked', async () => {
        const user = userEvent.setup();

        render(<FilterBySubset />, { route: '/projects/123', path: '/projects/:projectId' });

        const dialog = await openSubsetFilter(user);

        await user.click(within(dialog).getByRole('checkbox', { name: 'Select all items' }));

        await waitFor(() => {
            expect(screen.getByText('4 subsets selected')).toBeVisible();
        });

        expect(within(dialog).getByText('No subset')).toBeVisible();
        expect(within(dialog).getByText('Training subset')).toBeVisible();
        expect(within(dialog).getByText('Validation subset')).toBeVisible();
        expect(within(dialog).getByText('Testing subset')).toBeVisible();
    });
});
