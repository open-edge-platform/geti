// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from 'test-utils/render';

import { SUBSET_PARAM } from '../../../../../../hooks/use-dataset-filters-search-params.hook';
import { FilterBySubset } from './filter-by-subset.component';

describe('FilterBySubset', () => {
    it('shows a placeholder when no subset is selected', () => {
        render(<FilterBySubset />, { route: '/projects/123', path: '/projects/:projectId' });

        expect(screen.getByText('Filter by subset')).toBeVisible();
    });

    it('pre-checks the checkboxes for subsets selected via the search params', () => {
        render(<FilterBySubset />, {
            route: `/projects/123?${SUBSET_PARAM}=training,validation`,
            path: '/projects/:projectId',
        });

        expect(screen.getByRole('checkbox', { name: 'Training' })).toBeChecked();
        expect(screen.getByRole('checkbox', { name: 'Validation' })).toBeChecked();
        expect(screen.getByRole('checkbox', { name: 'Testing' })).not.toBeChecked();
        expect(screen.getByRole('checkbox', { name: 'Unassigned' })).not.toBeChecked();
    });

    it('allows selecting multiple subsets', async () => {
        const user = userEvent.setup();

        render(<FilterBySubset />, { route: '/projects/123', path: '/projects/:projectId' });

        await user.click(screen.getByRole('checkbox', { name: 'Training' }));
        await user.click(screen.getByRole('checkbox', { name: 'Testing' }));

        expect(screen.getByRole('checkbox', { name: 'Training' })).toBeChecked();
        expect(screen.getByRole('checkbox', { name: 'Testing' })).toBeChecked();
        expect(screen.getByRole('checkbox', { name: 'Validation' })).not.toBeChecked();
    });
});
