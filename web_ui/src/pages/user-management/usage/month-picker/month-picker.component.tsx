// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useRef } from 'react';

import { ActionButton, CustomPopover } from '@geti/ui';
import { Calendar } from '@geti/ui/icons';
import { CalendarProps } from '@react-aria/calendar';
import { DateValue } from 'react-aria';
import { useOverlayTriggerState } from 'react-stately';

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
