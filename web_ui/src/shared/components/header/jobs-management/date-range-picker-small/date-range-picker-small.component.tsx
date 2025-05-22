// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, ReactNode, useState } from 'react';

import {
    ActionButton,
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
} from '@geti/ui';
import { DateValue, getLocalTimeZone } from '@internationalized/date';
import Calendar from '@spectrum-icons/workflow/Calendar';
import { isFunction } from 'lodash-es';
import isEmpty from 'lodash/isEmpty';
import { RangeCalendarProps } from 'react-aria-components';

interface DateRangePickerSmall extends Omit<RangeCalendarProps<DateValue>, 'focusedValue' | 'onFocusChange'> {
    hasManualEdition?: boolean;
    headerContent?: ReactNode;
}

export const DateRangePickerSmall: FC<DateRangePickerSmall> = ({
    hasManualEdition,
    headerContent,
    value: range,
    onChange,
    ...props
}) => {
    const formatter = useDateFormatter({ dateStyle: 'long' });
    const [focusedDate, setFocusedDate] = useState<DateValue | undefined>();

    const rangeText = isEmpty(range)
        ? ''
        : formatter.formatRange(range.start.toDate(getLocalTimeZone()), range.end.toDate(getLocalTimeZone()));

    const handleOnChange = (attribute: 'start' | 'end', value: DateValue | null | undefined) => {
        if (isEmpty(value) || isEmpty(range)) {
            return;
        }

        isFunction(onChange) && onChange({ ...range, [attribute]: value });
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
                <ActionButton isQuiet aria-label='Select date range'>
                    <Calendar />
                </ActionButton>
                <Tooltip>{rangeText}</Tooltip>
            </TooltipTrigger>
            <Dialog>
                {headerContent ? <Heading>{headerContent}</Heading> : <></>}
                <Content>
                    <RangeCalendar
                        {...props}
                        value={range}
                        onChange={onChange}
                        focusedValue={focusedDate}
                        onFocusChange={setFocusedDate}
                    />
                    {hasManualEdition ? rangeFields : <p>{rangeText}</p>}
                </Content>
            </Dialog>
        </DialogTrigger>
    );
};
