// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

import { View } from '@adobe/react-spectrum';
import { DatePicker } from '@geti/ui';
import { DateValue, getLocalTimeZone, parseAbsolute, parseDateTime, today } from '@internationalized/date';

import { SearchRuleValue } from '../../../../core/media/media-filter.interface';
import { formatLocalToUtc, isDateBetween } from '../../../../shared/utils';

import classes from './media-filter-value-date.module.scss';

interface MediaFilterValueDateProps {
    value: string;
    onSelectionChange: (key: SearchRuleValue) => void;
}

const MIN_DATE = parseDateTime('2020-01-30');
const MAX_DATE = parseDateTime('9999-11-30');
const TODAY = today(getLocalTimeZone());
const replaceAllInBrackets = (text: string) => text.replace(/([\[(])(.+?)([\])])/g, '');

export const MediaFilterValueDate = ({ value: initVal, onSelectionChange }: MediaFilterValueDateProps): JSX.Element => {
    const [value, setValue] = useState<DateValue | undefined>(undefined);

    useEffect(() => {
        if (initVal === '') {
            setValue(undefined);
        } else {
            const absoluteDate = parseAbsolute(initVal, getLocalTimeZone());

            setValue(absoluteDate);
        }
    }, [initVal]);

    const onChange = (newValue: DateValue | null) => {
        if (newValue === null) {
            return;
        }

        const isValidDate = isDateBetween(newValue, MIN_DATE, MAX_DATE);
        isValidDate && onSelectionChange(formatLocalToUtc(replaceAllInBrackets(newValue.toString())));
    };

    return (
        <View UNSAFE_className={classes.mediaFilterDate}>
            <DatePicker
                isQuiet
                aria-label={'media filter date'}
                id={'media-filter-date'}
                placeholderValue={TODAY}
                value={value}
                onChange={onChange}
            />
        </View>
    );
};
