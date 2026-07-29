// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen, within } from '@testing-library/react';
import userEvent, { type UserEvent } from '@testing-library/user-event';
import { render } from 'test-utils/render';

import {
    END_DATE_PARAM,
    START_DATE_PARAM,
    useDatasetFiltersSearchParams,
} from '../../../../../../hooks/use-dataset-filters-search-params.hook';
import { DateFilter } from './date-filter.component';

const AppliedFilters = () => {
    const { startDate, endDate } = useDatasetFiltersSearchParams();

    return <div data-testid='applied-filters'>{`${startDate ?? 'none'}|${endDate ?? 'none'}`}</div>;
};

const renderDateFilter = (search = '') => {
    return render(
        <>
            <DateFilter />
            <AppliedFilters />
        </>,
        { route: `/projects/123${search}`, path: '/projects/:projectId' }
    );
};

const getYearSegment = (fieldName: string) => {
    return within(screen.getByRole('group', { name: fieldName })).getByRole('spinbutton', { name: /year/i });
};

// Fills every segment of a date field at once, the digits are expected to follow the
// en-US segment order: month, day, year, hour, minute, second
const typeDate = async (user: UserEvent, fieldName: string, digits: string) => {
    const [firstSegment] = within(screen.getByRole('group', { name: fieldName })).getAllByRole('spinbutton');

    await user.click(firstSegment);
    await user.keyboard(digits);
};

const getAppliedFilters = () => screen.getByTestId('applied-filters').textContent;

const START_DATE = '2024-05-10T10:00:00.000Z';
const END_DATE = '2024-06-10T10:00:00.000Z';

describe('DateFilter', () => {
    const search = `?${START_DATE_PARAM}=${START_DATE}&${END_DATE_PARAM}=${END_DATE}`;

    it('applies the filter properly', async () => {
        const user = userEvent.setup();

        renderDateFilter();

        await typeDate(user, 'Start date', '05102024100000');
        await typeDate(user, 'End date', '06102024120000');

        // The pickers operate in the local time zone, so the expected values are built the same way
        const expectedStartDate = new Date(2024, 4, 10, 10, 0, 0).toISOString();
        const expectedEndDate = new Date(2024, 5, 10, 12, 0, 0).toISOString();

        expect(getAppliedFilters()).toBe(`${expectedStartDate}|${expectedEndDate}`);
    });

    it('keeps the previously applied filters and shows an error when the end date is earlier than the start date', async () => {
        const user = userEvent.setup();

        renderDateFilter(search);

        await user.click(getYearSegment('End date'));
        await user.keyboard('2023');

        expect(await screen.findByText('End date must be later than start date')).toBeVisible();
        expect(getAppliedFilters()).toBe(`${START_DATE}|${END_DATE}`);
    });

    it('re-applies the filter once the range becomes valid again', async () => {
        const user = userEvent.setup();

        renderDateFilter(search);

        await user.click(getYearSegment('End date'));
        await user.keyboard('2023');

        expect(await screen.findByText('End date must be later than start date')).toBeVisible();

        await user.click(getYearSegment('End date'));
        await user.keyboard('2025');

        const expectedEndDate = new Date(END_DATE);
        expectedEndDate.setFullYear(2025);

        expect(screen.queryByText('End date must be later than start date')).not.toBeInTheDocument();
        expect(getAppliedFilters()).toBe(`${START_DATE}|${expectedEndDate.toISOString()}`);
    });
});
