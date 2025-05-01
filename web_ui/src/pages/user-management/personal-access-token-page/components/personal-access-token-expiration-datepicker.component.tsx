// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DateValue, getLocalTimeZone, parseDate, today } from '@internationalized/date';
import { DatePicker } from '@shared/components/date-picker/date-picker.component';
import { isDateBetween } from '@shared/utils';

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
