// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useMemo, useState } from 'react';

import { ActionButton, DatePicker, Flex, Text } from '@geti-ui/ui';
import {
    getLocalTimeZone,
    now,
    parseAbsoluteToLocal,
    toZoned,
    type DateValue,
    type ZonedDateTime,
} from '@internationalized/date';
import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';

import classes from './date-filter.module.scss';

const MIN_DATE = parseAbsoluteToLocal('2020-01-30T00:00:00.000Z');

export const INVALID_RANGE_MESSAGE = 'End date must be later than start date';

const parseDate = (date: string | null): ZonedDateTime | null => (date === null ? null : parseAbsoluteToLocal(date));

// An empty picker hands back a date without a timezone, so it has to be anchored to the local one
const toZonedDateTime = (date: DateValue | null): ZonedDateTime | null =>
    date === null ? null : toZoned(date, getLocalTimeZone());

const toISOString = (date: ZonedDateTime | null): string | null => (date === null ? null : date.toDate().toISOString());

export const DateFilter = () => {
    const { startDate, endDate, setDateRange } = useDatasetFiltersSearchParams();

    // Media cannot be uploaded in the future.
    const [maxDate] = useState(() =>
        now(getLocalTimeZone()).set({ hour: 23, minute: 59, second: 59, millisecond: 999 })
    );

    // Range picked by the user whose end date precedes its start date, and thus was not applied as a filter
    const [invalidRange, setInvalidRange] = useState<{ start: ZonedDateTime; end: ZonedDateTime } | null>(null);

    // Memoized so the pickers keep receiving the same value instance while the filter does not change
    const appliedStart = useMemo(() => parseDate(startDate), [startDate]);
    const appliedEnd = useMemo(() => parseDate(endDate), [endDate]);

    const startValue = invalidRange?.start ?? appliedStart;
    const endValue = invalidRange?.end ?? appliedEnd;

    const applyDates = (start: ZonedDateTime | null, end: ZonedDateTime | null) => {
        if (start !== null && end !== null && end.compare(start) < 0) {
            setInvalidRange({ start, end });

            return;
        }

        setInvalidRange(null);

        const newStartDate = toISOString(start);
        const newEndDate = toISOString(end);

        if (newStartDate !== startDate || newEndDate !== endDate) {
            setDateRange(newStartDate, newEndDate);
        }
    };

    const handleStartDateChange = (date: DateValue | null) => {
        applyDates(toZonedDateTime(date), endValue);
    };

    const handleEndDateChange = (date: DateValue | null) => {
        applyDates(startValue, toZonedDateTime(date));
    };

    const handleClear = () => {
        setInvalidRange(null);

        if (startDate !== null || endDate !== null) {
            setDateRange(null, null);
        }
    };

    return (
        <Flex direction='column' gap='size-100'>
            <Flex direction='row' alignItems='center' justifyContent='space-between'>
                <Text UNSAFE_className={classes.label}>Filter by upload date</Text>

                <ActionButton
                    isQuiet
                    aria-label='Clear upload date filter'
                    isDisabled={startValue === null && endValue === null}
                    onPress={handleClear}
                >
                    <Text>Clear</Text>
                </ActionButton>
            </Flex>

            <DatePicker
                granularity='minute'
                hourCycle={24}
                width='100%'
                label='Start date'
                labelPosition='top'
                minValue={MIN_DATE}
                maxValue={maxDate}
                value={startValue}
                onChange={handleStartDateChange}
            />

            <DatePicker
                granularity='minute'
                hourCycle={24}
                width='100%'
                label='End date'
                labelPosition='top'
                minValue={MIN_DATE}
                maxValue={maxDate}
                value={endValue}
                onChange={handleEndDateChange}
                validationState={invalidRange === null ? undefined : 'invalid'}
                errorMessage={invalidRange === null ? undefined : INVALID_RANGE_MESSAGE}
            />
        </Flex>
    );
};
