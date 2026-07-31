// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import { DateRangePicker } from '@geti-ui/ui';
import { getLocalTimeZone, now, parseAbsoluteToLocal, type ZonedDateTime } from '@internationalized/date';
import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';

import classes from './date-filter.module.scss';

type DateRange = { start: ZonedDateTime; end: ZonedDateTime };

const toDateRange = (start: string | null, end: string | null): DateRange | null =>
    start === null || end === null ? null : { start: parseAbsoluteToLocal(start), end: parseAbsoluteToLocal(end) };

const isDateRangeValid = ({ start, end }: DateRange, maxDate: ZonedDateTime): boolean =>
    end.compare(start) >= 0 && end.compare(maxDate) <= 0;

export const DateFilter = () => {
    const { startDate, endDate, setDateRange } = useDatasetFiltersSearchParams();

    const maxDate = now(getLocalTimeZone());

    // The picker is kept in local state so that an invalid range can be shown to the user
    // without being applied to the dataset filters
    const [range, setRange] = useState<DateRange | null>(() => toDateRange(startDate, endDate));

    const handleChange = (value: DateRange | null) => {
        setRange(value);

        if (value !== null && !isDateRangeValid(value, maxDate)) {
            return;
        }

        setDateRange(
            value === null ? null : value.start.toDate().toISOString(),
            value === null ? null : value.end.toDate().toISOString()
        );
    };

    return (
        <DateRangePicker
            label='Filter by upload date'
            labelPosition='top'
            width='100%'
            granularity='minute'
            hourCycle={24}
            hideTimeZone
            maxValue={maxDate}
            value={range}
            onChange={handleChange}
            UNSAFE_className={classes.dateRangePicker}
        />
    );
};
