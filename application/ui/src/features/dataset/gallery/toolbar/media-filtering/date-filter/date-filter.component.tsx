// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { DatePicker, Flex, Text } from '@geti-ui/ui';
import { getLocalTimeZone, parseAbsoluteToLocal, type DateValue } from '@internationalized/date';
import dayjs from 'dayjs';
import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';

import classes from './date-filter.module.scss';

const MIN_DATE = parseAbsoluteToLocal(dayjs('2020-01-30').startOf('d').toISOString());
const MAX_DATE = parseAbsoluteToLocal(dayjs('9999-11-30').endOf('d').toISOString());

export const DateFilter = () => {
    const { startDate, endDate, setStartDate, setEndDate } = useDatasetFiltersSearchParams();

    const handleStartDateChange = (date: DateValue | null) => {
        if (date === null) {
            return;
        }

        setStartDate(date.toDate(getLocalTimeZone()).toISOString());
    };

    const handleEndDateChange = (date: DateValue | null) => {
        if (date === null) {
            return;
        }

        setEndDate(date.toDate(getLocalTimeZone()).toISOString());
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
                    maxValue={endDate === null ? MAX_DATE : parseAbsoluteToLocal(endDate)}
                    value={startDate === null ? null : parseAbsoluteToLocal(startDate)}
                    onChange={handleStartDateChange}
                />

                <DatePicker
                    granularity={'second'}
                    width={'100%'}
                    label='End date'
                    labelPosition={'top'}
                    hourCycle={24}
                    minValue={startDate === null ? MIN_DATE : parseAbsoluteToLocal(startDate)}
                    maxValue={MAX_DATE}
                    value={endDate === null ? null : parseAbsoluteToLocal(endDate)}
                    onChange={handleEndDateChange}
                />
            </Flex>
        </Flex>
    );
};
