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

// Both date fields live in a single group, their segments are told apart by the
// "Start Date" / "End Date" part of their accessible name
const getSegment = (segmentName: RegExp) => screen.getByRole('spinbutton', { name: segmentName });

// Fills every segment of a date field at once, the digits are expected to follow the
// en-US segment order: month, day, year
const typeDate = async (user: UserEvent, fieldName: 'start' | 'end', digits: string) => {
    await user.click(getSegment(new RegExp(`month, ${fieldName} date`, 'i')));
    await user.keyboard(digits);
};

const getAppliedFilters = () => screen.getByTestId('applied-filters').textContent;

const START_DATE = '2024-05-10T10:00:00.000Z';
const END_DATE = '2024-06-10T10:00:00.000Z';

// The picker works with local calendar days, the applied filters span the whole day
const startOfLocalDay = (year: number, month: number, day: number) => new Date(year, month, day).toISOString();
const endOfLocalDay = (year: number, month: number, day: number) =>
    new Date(year, month, day, 23, 59, 59, 999).toISOString();

describe('DateFilter', () => {
    const search = `?${START_DATE_PARAM}=${START_DATE}&${END_DATE_PARAM}=${END_DATE}`;

    it('applies the filter properly', async () => {
        const user = userEvent.setup();

        renderDateFilter();

        await typeDate(user, 'start', '05102024');
        await typeDate(user, 'end', '06102024');

        expect(getAppliedFilters()).toBe(`${startOfLocalDay(2024, 4, 10)}|${endOfLocalDay(2024, 5, 10)}`);
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

        const startDate = new Date(START_DATE);
        const endDate = new Date(END_DATE);

        expect(screen.queryByText(REVERSED_RANGE_MESSAGE)).not.toBeInTheDocument();
        expect(getAppliedFilters()).toBe(
            [
                startOfLocalDay(startDate.getFullYear(), startDate.getMonth(), startDate.getDate()),
                endOfLocalDay(2025, endDate.getMonth(), endDate.getDate()),
            ].join('|')
        );
    });
});
