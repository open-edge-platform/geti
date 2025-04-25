// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
