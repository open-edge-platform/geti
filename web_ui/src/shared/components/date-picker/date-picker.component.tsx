// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DatePicker as SpectrumDatePicker, SpectrumDatePickerProps } from '@adobe/react-spectrum';
import { DateValue } from '@internationalized/date';

// For more information about this component: https://react-spectrum.adobe.com/react-spectrum/DatePicker.html
export const DatePicker = (props: SpectrumDatePickerProps<DateValue>) => {
    // Width set due to layout flickering issue on datepicker on mobile Safari
    return <SpectrumDatePicker width={'size-2400'} {...props} />;
};
