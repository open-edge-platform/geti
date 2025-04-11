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

import { CalendarProps } from '@react-aria/calendar';
import Calendar from '@spectrum-icons/workflow/Calendar';
import { DateValue } from 'react-aria';
import { useOverlayTriggerState } from 'react-stately';

import { ActionButton } from '../button/button.component';
import { CustomPopover } from '../custom-popover/custom-popover.component';
import { MonthCalendar } from './month-calendar.component';

interface MonthPickerProps extends CalendarProps<DateValue> {
    isButtonQuiet?: boolean;
}

export const MonthPicker = (props: MonthPickerProps): JSX.Element => {
    const ref = useRef(null);
    const state = useOverlayTriggerState({});
    return (
        <>
            <ActionButton aria-label='Select a month' ref={ref} onPress={state.toggle} isQuiet={props.isButtonQuiet}>
                <Calendar />
            </ActionButton>
            <CustomPopover ref={ref} state={state} placement='bottom' UNSAFE_style={{ border: 'none' }}>
                <MonthCalendar margin={'size-300'} marginTop={'size-100'} {...props} />
            </CustomPopover>
        </>
    );
};
