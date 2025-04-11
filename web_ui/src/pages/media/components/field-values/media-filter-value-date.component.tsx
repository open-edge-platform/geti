// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect, useState } from 'react';

import { DateValue, getLocalTimeZone, parseAbsolute, parseDateTime, today } from '@internationalized/date';
import { View } from '@react-spectrum/view';

import { SearchRuleValue } from '../../../../core/media/media-filter.interface';
import { DatePicker } from '../../../../shared/components/date-picker/date-picker.component';
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
