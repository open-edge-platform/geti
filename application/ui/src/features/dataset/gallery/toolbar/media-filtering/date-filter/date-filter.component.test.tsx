// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useSearchParams } from 'react-router-dom';
import { render } from 'test-utils/render';

import { END_DATE_PARAM, START_DATE_PARAM } from '../../../../../../hooks/use-dataset-filters-search-params.hook';
import { DateFilter } from './date-filter.component';

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

const setYear = async (user: ReturnType<typeof userEvent.setup>, fieldName: string, year: string) => {
    const field = screen.getByRole('group', { name: fieldName });
    const yearSegment = within(field).getByRole('spinbutton', { name: /year/i });

    await user.click(yearSegment);
    await user.keyboard(year);
};

describe('DateFilter', () => {
    const routeWithDates = `/projects/123?${START_DATE_PARAM}=${START_DATE}&${END_DATE_PARAM}=${END_DATE}`;

    it('does not apply the filter when the end date precedes the start date', async () => {
        const user = userEvent.setup();

        renderDateFilter(routeWithDates);

        await setYear(user, 'End date', '2020');

        expect(screen.getByTestId('applied-start-date')).toHaveTextContent(START_DATE);
        expect(screen.getByTestId('applied-end-date')).toHaveTextContent(END_DATE);
    });

    it('applies the filter once the range becomes valid again', async () => {
        const user = userEvent.setup();

        renderDateFilter(routeWithDates);

        await setYear(user, 'End date', '2020');
        await setYear(user, 'Start date', '2020');

        expect(screen.getByTestId('applied-start-date')).toHaveTextContent('2020-03-15');
        expect(screen.getByTestId('applied-end-date')).toHaveTextContent('2020-03-20');
    });

    it('applies the filter when the picked range is valid', async () => {
        const user = userEvent.setup();

        renderDateFilter(routeWithDates);

        await setYear(user, 'Start date', '2025');

        expect(screen.getByTestId('applied-start-date')).toHaveTextContent('2025-03-15');
    });
});
