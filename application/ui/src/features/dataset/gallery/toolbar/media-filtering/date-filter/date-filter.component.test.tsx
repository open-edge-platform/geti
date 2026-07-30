// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen } from '@testing-library/react';
import userEvent, { type UserEvent } from '@testing-library/user-event';
import { render } from 'test-utils/render';

import {
    END_DATE_PARAM,
    START_DATE_PARAM,
    useDatasetFiltersSearchParams,
} from '../../../../../../hooks/use-dataset-filters-search-params.hook';
import { DateFilter } from './date-filter.component';

const REVERSED_RANGE_MESSAGE = 'Start date must be before end date.';

const AppliedFilters = () => {
    const { startDate, endDate, setDateRange } = useDatasetFiltersSearchParams();

    return (
        <>
            <div data-testid='applied-filters'>{`${startDate ?? 'none'}|${endDate ?? 'none'}`}</div>
            <button onClick={() => setDateRange(null, null)}>Clear all</button>
        </>
    );
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

// Both date fields live in a single group, their segments are told apart by the
// "Start Date" / "End Date" part of their accessible name
const getSegment = (segmentName: RegExp) => screen.getByRole('spinbutton', { name: segmentName });

// Fills every segment of a date field at once, the digits are expected to follow the
// en-US segment order: month, day, year, hour, minute
const typeDate = async (user: UserEvent, fieldName: 'start' | 'end', digits: string) => {
    await user.click(getSegment(new RegExp(`month, ${fieldName} date`, 'i')));
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

        await typeDate(user, 'start', '051020241000');
        await typeDate(user, 'end', '061020241200');

        // The picker operates in the local time zone, so the expected values are built the same way
        const expectedStartDate = new Date(2024, 4, 10, 10, 0).toISOString();
        const expectedEndDate = new Date(2024, 5, 10, 12, 0).toISOString();

        expect(getAppliedFilters()).toBe(`${expectedStartDate}|${expectedEndDate}`);
    });

    it('does not allow filtering by a date in the future', async () => {
        const user = userEvent.setup();

        renderDateFilter(search);

        await user.click(getSegment(/year, end date/i));
        await user.keyboard(String(new Date().getFullYear() + 1));

        expect(await screen.findByText(/or earlier\.$/)).toBeVisible();
        expect(getAppliedFilters()).toBe(`${START_DATE}|${END_DATE}`);
    });

    it('keeps the previously applied filters and shows an error when the end date is earlier than the start date', async () => {
        const user = userEvent.setup();

        renderDateFilter(search);

        await user.click(getSegment(/year, end date/i));
        await user.keyboard('2023');

        expect(await screen.findByText(REVERSED_RANGE_MESSAGE)).toBeVisible();
        expect(getAppliedFilters()).toBe(`${START_DATE}|${END_DATE}`);
    });

    it('re-applies the filter once the range becomes valid again', async () => {
        const user = userEvent.setup();

        renderDateFilter(search);

        await user.click(getSegment(/year, end date/i));
        await user.keyboard('2023');

        expect(await screen.findByText(REVERSED_RANGE_MESSAGE)).toBeVisible();

        await user.click(getSegment(/year, end date/i));
        await user.keyboard('2025');

        const expectedEndDate = new Date(END_DATE);
        expectedEndDate.setFullYear(2025);

        expect(screen.queryByText(REVERSED_RANGE_MESSAGE)).not.toBeInTheDocument();
        expect(getAppliedFilters()).toBe(`${START_DATE}|${expectedEndDate.toISOString()}`);
    });

    it('resets the picker when the filters are cleared elsewhere', async () => {
        const user = userEvent.setup();

        renderDateFilter(search);

        expect(getSegment(/year, start date/i)).toHaveTextContent('2024');

        await user.click(screen.getByRole('button', { name: 'Clear all' }));

        expect(getAppliedFilters()).toBe('none|none');
        expect(getSegment(/year, start date/i)).toHaveTextContent('yyyy');
    });
});
