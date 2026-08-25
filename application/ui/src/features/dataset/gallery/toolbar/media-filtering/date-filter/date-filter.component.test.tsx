// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useSearchParams } from 'react-router-dom';
import { render } from 'test-utils/render';

import { END_DATE_PARAM, START_DATE_PARAM } from '../../../../../../hooks/use-dataset-filters-search-params.hook';
import { DateFilter, INVALID_RANGE_MESSAGE } from './date-filter.component';

const START_DATE = '2026-03-15T10:00:00.000Z';
const END_DATE = '2026-03-20T10:00:00.000Z';

const AppliedFilters = () => {
    const [searchParams] = useSearchParams();

    return (
        <>
            <span data-testid='applied-start-date'>{searchParams.get(START_DATE_PARAM) ?? ''}</span>
            <span data-testid='applied-end-date'>{searchParams.get(END_DATE_PARAM) ?? ''}</span>
        </>
    );
};

const renderDateFilter = (route: string) =>
    render(
        <>
            <DateFilter />
            <AppliedFilters />
        </>,
        { route, path: '/projects/:projectId' }
    );

const setSegment = async (
    user: ReturnType<typeof userEvent.setup>,
    fieldName: string,
    segmentName: RegExp,
    value: string
) => {
    const field = screen.getByRole('group', { name: fieldName });
    const segment = within(field).getByRole('spinbutton', { name: segmentName });

    await user.click(segment);
    await user.keyboard(value);
};

const setYear = (user: ReturnType<typeof userEvent.setup>, fieldName: string, year: string) =>
    setSegment(user, fieldName, /year/i, year);

// A month is committed with a single keystroke, so it does not go through intermediate (applied) values
const setMonth = (user: ReturnType<typeof userEvent.setup>, fieldName: string, month: string) =>
    setSegment(user, fieldName, /month/i, month);

describe('DateFilter', () => {
    const routeWithDates = `/projects/123?${START_DATE_PARAM}=${START_DATE}&${END_DATE_PARAM}=${END_DATE}`;

    it('applies the filter when the picked range is valid', async () => {
        const user = userEvent.setup();

        renderDateFilter(routeWithDates);

        await setYear(user, 'Start date', '2025');

        expect(screen.getByTestId('applied-start-date')).toHaveTextContent('2025-03-15');
        expect(screen.getByTestId('applied-end-date')).toHaveTextContent(END_DATE);
        expect(screen.queryByText(INVALID_RANGE_MESSAGE)).not.toBeInTheDocument();
    });

    it('keeps the previous filter and shows an error when the end date is moved before the start date', async () => {
        const user = userEvent.setup();

        renderDateFilter(routeWithDates);

        await setYear(user, 'End date', '2020');

        expect(screen.getByTestId('applied-start-date')).toHaveTextContent(START_DATE);
        expect(screen.getByTestId('applied-end-date')).toHaveTextContent(END_DATE);
        expect(screen.getByText(INVALID_RANGE_MESSAGE)).toBeVisible();
    });

    it('keeps the previous filter and shows an error when the start date is moved after the end date', async () => {
        const user = userEvent.setup();

        renderDateFilter(routeWithDates);

        await setMonth(user, 'Start date', '4');

        expect(screen.getByTestId('applied-start-date')).toHaveTextContent(START_DATE);
        expect(screen.getByTestId('applied-end-date')).toHaveTextContent(END_DATE);
        expect(screen.getByText(INVALID_RANGE_MESSAGE)).toBeVisible();
    });

    it('applies the filter once an invalid end date is corrected', async () => {
        const user = userEvent.setup();

        renderDateFilter(routeWithDates);

        await setYear(user, 'End date', '2020');
        await setYear(user, 'Start date', '2020');

        expect(screen.getByTestId('applied-start-date')).toHaveTextContent('2020-03-15');
        expect(screen.getByTestId('applied-end-date')).toHaveTextContent('2020-03-20');
        expect(screen.queryByText(INVALID_RANGE_MESSAGE)).not.toBeInTheDocument();
    });

    it('applies the filter once an invalid start date is corrected', async () => {
        const user = userEvent.setup();

        renderDateFilter(routeWithDates);

        await setMonth(user, 'Start date', '4');
        await setMonth(user, 'Start date', '2');

        expect(screen.getByTestId('applied-start-date')).toHaveTextContent('2026-02-15');
        expect(screen.getByTestId('applied-end-date')).toHaveTextContent(END_DATE);
        expect(screen.queryByText(INVALID_RANGE_MESSAGE)).not.toBeInTheDocument();
    });
});
