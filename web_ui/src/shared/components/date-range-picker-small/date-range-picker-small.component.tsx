// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, ReactNode, useEffect, useState } from 'react';

import {
    Content,
    DateField,
    Dialog,
    DialogTrigger,
    Flex,
    Heading,
    RangeCalendar,
    Tooltip,
    TooltipTrigger,
    useDateFormatter,
} from '@adobe/react-spectrum';
import { DateValue, getLocalTimeZone } from '@internationalized/date';
import { RangeValue } from '@react-types/shared';
import Calendar from '@spectrum-icons/workflow/Calendar';
import isEmpty from 'lodash/isEmpty';
import { RangeCalendarProps } from 'react-aria-components';

import { QuietActionButton } from '../quiet-button/quiet-action-button.component';

interface DateRangePickerSmall extends RangeCalendarProps<DateValue> {
    hasManualEdition?: boolean;
    headerContent?: ReactNode;
}

export const DateRangePickerSmall: FC<DateRangePickerSmall> = ({ hasManualEdition, headerContent, ...props }) => {
    const formatter = useDateFormatter({ dateStyle: 'long' });
    const [range, setRange] = useState<RangeValue<DateValue>>();
    const [focusedDate, setFocusedDate] = useState<DateValue | undefined>();

    const rangeText = isEmpty(range)
        ? ''
        : formatter.formatRange(range.start.toDate(getLocalTimeZone()), range.end.toDate(getLocalTimeZone()));

    useEffect(() => {
        !isEmpty(props.value) && setRange(props.value);
    }, [props.value]);

    const handleOnChange = (attribute: 'start' | 'end', value: DateValue | null | undefined) => {
        if (isEmpty(value) || isEmpty(range)) {
            return;
        }

        setRange({ ...range, [attribute]: value });
        setFocusedDate(value);
    };

    const rangeFields = (
        <Flex gap={'size-50'}>
            <DateField
                isQuiet={false}
                label='From'
                value={range?.start}
                onChange={(value) => handleOnChange('start', value)}
            />
            <DateField
                isQuiet={false}
                label='To'
                value={range?.end}
                onChange={(value) => handleOnChange('end', value)}
            />
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
                <Heading>{headerContent}</Heading>
                <Content>
                    <RangeCalendar {...props} value={range} focusedValue={focusedDate} onFocusChange={setFocusedDate} />
                    {hasManualEdition ? rangeFields : <p>{rangeText}</p>}
                </Content>
            </Dialog>
        </DialogTrigger>
    );
};
