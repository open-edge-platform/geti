// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import { DatePicker, Flex, Text } from '@geti-ui/ui';
import { parseAbsoluteToLocal, type ZonedDateTime } from '@internationalized/date';
import dayjs from 'dayjs';
import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';

import classes from './date-filter.module.scss';

const MIN_DATE = parseAbsoluteToLocal(dayjs('2020-01-30').startOf('d').toISOString());
const MAX_DATE = parseAbsoluteToLocal(dayjs('9999-11-30').endOf('d').toISOString());

const INVALID_RANGE_MESSAGE = 'End date must be later than start date';

const toDateValue = (date: string | null): ZonedDateTime | null => (date === null ? null : parseAbsoluteToLocal(date));

const toISOString = (date: ZonedDateTime): string => date.toDate().toISOString();

const isInvalidRange = (start: ZonedDateTime | null, end: ZonedDateTime | null): boolean =>
    start !== null && end !== null && end.compare(start) < 0;

export const DateFilter = () => {
    const { startDate, endDate, setStartDate, setEndDate } = useDatasetFiltersSearchParams();

    // The pickers are kept in local state so that an invalid range can be shown to the user
    // without being applied to the dataset filters
    const [localStartDate, setLocalStartDate] = useState<ZonedDateTime | null>(() => toDateValue(startDate));
    const [localEndDate, setLocalEndDate] = useState<ZonedDateTime | null>(() => toDateValue(endDate));

    const hasInvalidRange = isInvalidRange(localStartDate, localEndDate);

    const applyFilters = (start: ZonedDateTime | null, end: ZonedDateTime | null) => {
        // An invalid range is never written to the search params, the previously applied
        // filters are kept untouched until the user enters a valid range again
        if (isInvalidRange(start, end)) {
            return;
        }

        setStartDate(start === null ? null : toISOString(start));
        setEndDate(end === null ? null : toISOString(end));
    };

    const handleStartDateChange = (date: ZonedDateTime | null) => {
        setLocalStartDate(date);

        applyFilters(date, localEndDate);
    };

    const handleEndDateChange = (date: ZonedDateTime | null) => {
        setLocalEndDate(date);

        applyFilters(localStartDate, date);
    };

    return (
        <Flex direction='column' gap='size-100'>
            <Text UNSAFE_className={classes.label}>Filter by upload date</Text>

            <Flex direction='column' gap='size-100'>
                <DatePicker
                    granularity={'second'}
                    width={'100%'}
                    label='Start date'
                    labelPosition={'top'}
                    hourCycle={24}
                    minValue={MIN_DATE}
                    maxValue={MAX_DATE}
                    value={localStartDate}
                    onChange={handleStartDateChange}
                    validationState={hasInvalidRange ? 'invalid' : undefined}
                />

                <DatePicker
                    granularity={'second'}
                    width={'100%'}
                    label='End date'
                    labelPosition={'top'}
                    hourCycle={24}
                    minValue={MIN_DATE}
                    maxValue={MAX_DATE}
                    value={localEndDate}
                    onChange={handleEndDateChange}
                    validationState={hasInvalidRange ? 'invalid' : undefined}
                    errorMessage={hasInvalidRange ? INVALID_RANGE_MESSAGE : undefined}
                />
            </Flex>
        </Flex>
    );
};
