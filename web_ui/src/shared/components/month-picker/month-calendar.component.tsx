// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useRef } from 'react';

import { Flex, Grid, Heading, repeat, useDateFormatter, View } from '@adobe/react-spectrum';
import { createCalendar } from '@internationalized/date';
import { CalendarProps, DateValue, useCalendar } from '@react-aria/calendar';
import { useLocale } from '@react-aria/i18n';
import { useCalendarState } from '@react-stately/calendar';
import { DOMRefValue, StyleProps } from '@react-types/shared';
import ChevronLeft from '@spectrum-icons/workflow/ChevronLeft';
import ChevronRight from '@spectrum-icons/workflow/ChevronRight';
import range from 'lodash/range';

import { ActionButton } from '../button/button.component';
import { CalendarCell } from './calendar-cell.component';

export const MonthCalendar = (props: CalendarProps<DateValue> & StyleProps): JSX.Element => {
    const { locale } = useLocale();
    const state = useCalendarState({ ...props, locale, createCalendar, visibleDuration: { years: 1 } });
    const ref = useRef<DOMRefValue>(null);
    const { calendarProps, nextButtonProps, prevButtonProps } = useCalendar(props, state);
    const yearDateFormatter = useDateFormatter({ year: 'numeric', timeZone: state.timeZone });
    return (
        <View {...calendarProps} {...props} ref={ref}>
            <Flex justifyContent={'space-between'} alignItems={'center'}>
                <ActionButton {...prevButtonProps} isQuiet>
                    <ChevronLeft />
                </ActionButton>
                <Heading level={2}>{yearDateFormatter.format(state.focusedDate.toDate(state.timeZone))}</Heading>
                <ActionButton {...nextButtonProps} isQuiet>
                    <ChevronRight />
                </ActionButton>
            </Flex>
            <Grid columns={repeat(4, '1fr')} alignContent={'center'}>
                {range(1, 13).map((month) => (
                    <CalendarCell key={month} state={state} date={state.focusedDate.set({ month })} month={month} />
                ))}
            </Grid>
        </View>
    );
};
