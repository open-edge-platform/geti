// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import {
    Content,
    Dialog,
    DialogTrigger,
    RangeCalendar,
    Tooltip,
    TooltipTrigger,
    useDateFormatter,
} from '@adobe/react-spectrum';
import { DateValue, getLocalTimeZone } from '@internationalized/date';
import Calendar from '@spectrum-icons/workflow/Calendar';
import { RangeCalendarProps } from 'react-aria';

import { QuietActionButton } from '../quiet-button/quiet-action-button.component';

export const DateRangePickerSmall = (props: RangeCalendarProps<DateValue>) => {
    const formatter = useDateFormatter({ dateStyle: 'long' });

    const rangeText = !!props.value
        ? formatter.formatRange(
              props.value.start.toDate(getLocalTimeZone()),
              props.value.end.toDate(getLocalTimeZone())
          )
        : '';

    return (
        <DialogTrigger type='popover'>
            <TooltipTrigger placement={'bottom'}>
                <QuietActionButton aria-label='Select date range'>
                    <Calendar />
                </QuietActionButton>
                <Tooltip>{rangeText}</Tooltip>
            </TooltipTrigger>
            <Dialog>
                <Content>
                    <RangeCalendar {...props} />
                    <p>{rangeText}</p>
                </Content>
            </Dialog>
        </DialogTrigger>
    );
};
