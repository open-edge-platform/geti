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

import { DateValue, getLocalTimeZone, parseDate, today } from '@internationalized/date';

import { DatePicker } from '../../../../shared/components/date-picker/date-picker.component';
import { isDateBetween } from '../../../../shared/utils';

interface PersonalAccessTokenExpirationDatepickerProps {
    setDate: (newExpirationDate: Date | null) => void;
    placeholderDate?: string;
}

// Dates in CalendarDate format
const MIN_DATE = today(getLocalTimeZone());
const MAX_DATE = parseDate('9999-11-30');

export const PersonalAccessTokenExpirationDatepicker = ({
    setDate,
    placeholderDate,
}: PersonalAccessTokenExpirationDatepickerProps) => {
    const handleOnChange = (newValue: DateValue | null) => {
        if (newValue === null) {
            return;
        }

        // When passing the value back to the parent, we need to convert the CalendarDate back
        // to native Date
        const newValuesAsNativeDate = newValue.toDate(getLocalTimeZone());

        const isValidDate = isDateBetween(newValue, MIN_DATE, MAX_DATE);

        // To control the 'disabled' state on the 'Create' button
        setDate(isValidDate ? newValuesAsNativeDate : null);
    };

    return (
        <div data-testid={'date-range-picker-box'} id={'date-range-picker-box-id'}>
            <DatePicker
                label={'Expiration date'}
                defaultValue={placeholderDate ? parseDate(placeholderDate) : undefined}
                minValue={MIN_DATE}
                maxValue={MAX_DATE}
                onChange={handleOnChange}
                width={'100%'}
                id={'pat-datepicker-id'}
                isRequired
            />
        </div>
    );
};
