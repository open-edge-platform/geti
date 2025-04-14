// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DateRangePicker as SpectrumDateRangePicker, SpectrumDateRangePickerProps } from '@adobe/react-spectrum';
import { DateValue } from '@internationalized/date';

// For more information about this component: https://react-spectrum.adobe.com/react-spectrum/DateRangePicker.html
export const DateRangePicker = (props: SpectrumDateRangePickerProps<DateValue>) => {
    return <SpectrumDateRangePicker {...props} />;
};
