// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import { DatePicker, Flex, Text } from '@geti-ui/ui';
import { getLocalTimeZone, now, parseAbsoluteToLocal, type ZonedDateTime } from '@internationalized/date';
import dayjs from 'dayjs';
import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';

import classes from './date-filter.module.scss';

const MIN_DATE = parseAbsoluteToLocal(dayjs('2020-01-30').startOf('d').toISOString());

export const INVALID_RANGE_MESSAGE = 'End date must be later than start date';

const parseDate = (date: string | null): ZonedDateTime | null => (date === null ? null : parseAbsoluteToLocal(date));

export const DateFilter = () => {
    const { startDate, endDate, setDateRange } = useDatasetFiltersSearchParams();

    // Media cannot be uploaded in the future
    const maxDate = now(getLocalTimeZone());

    // Range picked by the user whose end date precedes its start date, and thus was not applied as a filter
    const [invalidRange, setInvalidRange] = useState<{ start: ZonedDateTime; end: ZonedDateTime } | null>(null);

    const startValue = invalidRange?.start ?? parseDate(startDate);
    const endValue = invalidRange?.end ?? parseDate(endDate);

    const applyDates = (start: ZonedDateTime | null, end: ZonedDateTime | null) => {
        if (start !== null && end !== null && end.compare(start) < 0) {
            setInvalidRange({ start, end });

            return;
        }

        setInvalidRange(null);

        const newStartDate = start === null ? null : start.toDate().toISOString();
        const newEndDate = end === null ? null : end.toDate().toISOString();

        if (newStartDate !== startDate || newEndDate !== endDate) {
            setDateRange(newStartDate, newEndDate);
        }
    };

    const handleStartDateChange = (date: ZonedDateTime | null) => {
        applyDates(date, endValue);
    };

    const handleEndDateChange = (date: ZonedDateTime | null) => {
        applyDates(startValue, date);
    };

    return (
        <Flex direction='column' gap='size-100'>
            <Text UNSAFE_className={classes.label}>Filter by upload date</Text>

            <Flex direction='column' gap='size-100'>
                <DatePicker
                    granularity={'minute'}
                    width={'100%'}
                    label='Start date'
                    labelPosition={'top'}
                    hourCycle={24}
                    minValue={MIN_DATE}
                    maxValue={endValue}
                    value={startValue}
                    onChange={handleStartDateChange}
                />

                <DatePicker
                    granularity={'minute'}
                    width={'100%'}
                    label='End date'
                    labelPosition={'top'}
                    hourCycle={24}
                    minValue={startValue}
                    maxValue={maxDate}
                    value={endValue}
                    onChange={handleEndDateChange}
                    validationState={invalidRange === null ? undefined : 'invalid'}
                    errorMessage={INVALID_RANGE_MESSAGE}
                />
            </Flex>
        </Flex>
    );
};
