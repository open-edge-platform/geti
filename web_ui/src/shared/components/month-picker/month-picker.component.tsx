// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
