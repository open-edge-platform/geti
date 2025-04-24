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

import { useEffect, useState } from 'react';

import {
    Content,
    DateField,
    Dialog,
    DialogTrigger,
    Flex,
    RangeCalendar,
    Tooltip,
    TooltipTrigger,
    useDateFormatter,
} from '@adobe/react-spectrum';
import { DateValue, getLocalTimeZone } from '@internationalized/date';
import Calendar from '@spectrum-icons/workflow/Calendar';
import { RangeCalendarProps } from 'react-aria-components';

import { QuietActionButton } from '../quiet-button/quiet-action-button.component';

interface DateRangePickerSmall extends RangeCalendarProps<DateValue> {
    hasManualEdition?: boolean;
}

export const DateRangePickerSmall = ({ hasManualEdition, ...props }: DateRangePickerSmall) => {
    const formatter = useDateFormatter({ dateStyle: 'long' });
    const [start, setStart] = useState<DateValue | undefined>();
    const [end, setEnd] = useState<DateValue | undefined>();

    const rangeText =
        !!start && !!end ? formatter.formatRange(start.toDate(getLocalTimeZone()), end.toDate(getLocalTimeZone())) : '';

    const saveRange = () => {
        start && end && props.onChange && props.onChange({ ...props.value, start, end });
    };

    useEffect(() => {
        setStart(props.value?.start);
        setEnd(props.value?.end);
    }, [props.value]);

    const tmp = (
        <Flex gap={'size-50'}>
            <DateField
                isQuiet={false}
                label='From'
                value={start}
                onChange={(value) => value && setStart(value)}
                onBlur={saveRange}
            />
            <DateField isQuiet={false} label='To' value={end} onChange={(value) => value && setEnd(value)} />
        </Flex>
    );

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
                    {hasManualEdition ? tmp : <p>{rangeText}</p>}
                </Content>
            </Dialog>
        </DialogTrigger>
    );
};
