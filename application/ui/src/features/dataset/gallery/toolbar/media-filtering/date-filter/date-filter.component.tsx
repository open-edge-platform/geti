// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import { DateRangePicker } from '@geti-ui/ui';
import {
    getLocalTimeZone,
    parseAbsoluteToLocal,
    parseDate,
    Time,
    toCalendarDate,
    toCalendarDateTime,
    today,
    type CalendarDate,
} from '@internationalized/date';
import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';

type DateRange = { start: CalendarDate; end: CalendarDate };

const MIN_DATE = parseDate('2020-01-01');
const END_OF_DAY = new Time(23, 59, 59, 999);

const toDateRange = (start: string | null, end: string | null): DateRange | null =>
    start === null || end === null
        ? null
        : { start: toCalendarDate(parseAbsoluteToLocal(start)), end: toCalendarDate(parseAbsoluteToLocal(end)) };

const toStartOfDay = (date: CalendarDate): string => date.toDate(getLocalTimeZone()).toISOString();

const toEndOfDay = (date: CalendarDate): string =>
    toCalendarDateTime(date, END_OF_DAY).toDate(getLocalTimeZone()).toISOString();

const isApplicable = ({ start, end }: DateRange, maxDate: CalendarDate): boolean =>
    end.compare(start) >= 0 && start.compare(MIN_DATE) >= 0 && end.compare(maxDate) <= 0;

export const DateFilter = () => {
    const { startDate, endDate, setStartDate, setEndDate } = useDatasetFiltersSearchParams();

    // The picker is kept in local state so that an invalid range can be shown to the user
    // without being applied to the dataset filters
    const [range, setRange] = useState<DateRange | null>(() => toDateRange(startDate, endDate));

    const maxDate = today(getLocalTimeZone());

    const handleChange = (value: DateRange | null) => {
        setRange(value);

        if (value !== null && !isApplicable(value, maxDate)) {
            return;
        }

        setStartDate(value === null ? null : toStartOfDay(value.start));
        setEndDate(value === null ? null : toEndOfDay(value.end));
    };

    return (
        <DateRangePicker
            label='Filter by upload date'
            labelPosition='top'
            width='100%'
            granularity='minute'
            minValue={MIN_DATE}
            maxValue={maxDate}
            value={range}
            onChange={handleChange}
        />
    );
};
