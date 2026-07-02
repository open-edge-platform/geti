// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { DatePicker, Flex } from '@geti-ui/ui';
import { getLocalTimeZone, parseAbsoluteToLocal, type DateValue } from '@internationalized/date';
import dayjs from 'dayjs';
import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';

import { FilterPopoverButton } from '../../../../../components/filter-popover-button/filter-popover-button.component';
import { formatFilterDate } from '../../../../../shared/date-utils';

const MIN_DATE = parseAbsoluteToLocal(dayjs('2020-01-30').startOf('d').toISOString());
const MAX_DATE = parseAbsoluteToLocal(dayjs('9999-11-30').endOf('d').toISOString());

export const DateFilter = () => {
    const { startDate, endDate, setStartDate, setEndDate } = useDatasetFiltersSearchParams();

    const dates = [
        ...(startDate ? [{ id: 'startDate', name: `Start: ${formatFilterDate(startDate)}` }] : []),
        ...(endDate ? [{ id: 'endDate', name: `End: ${formatFilterDate(endDate)}` }] : []),
    ];

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
        <FilterPopoverButton
            ariaLabel='Filter by date'
            placeholder='Filter by upload date'
            summary={dates.length > 0 ? dates.map(({ name }) => name).join(', ') : null}
            gap='size-75'
            minWidth='size-2400'
            maxWidth='size-5000'
            dialogMaxWidth='size-3600'
        >
            <Flex direction='column' gap='size-200'>
                <DatePicker
                    granularity={'second'}
                    width={'100%'}
                    label='Start date'
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
                    hourCycle={24}
                    minValue={startDate === null ? MIN_DATE : parseAbsoluteToLocal(startDate)}
                    maxValue={MAX_DATE}
                    value={endDate === null ? null : parseAbsoluteToLocal(endDate)}
                    onChange={handleEndDateChange}
                />
            </Flex>
        </FilterPopoverButton>
    );
};
