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

import { SearchRuleValue } from '../../../../core/media/media-filter.interface';
import { useDebouncedCallback } from '../../../../hooks/use-debounced-callback/use-debounced-callback.hook';
import { CustomNumberField } from '../../../../shared/components/configurable-parameters/cp-item/custom-number-field/custom-number-field.component';

interface MediaFilterValueShapeAreaPercentageProps {
    value?: SearchRuleValue;
    isDisabled?: boolean;
    onSelectionChange: (key: SearchRuleValue) => void;
}

export const MediaFilterValueShapeAreaPercentage = ({
    value,
    isDisabled,
    onSelectionChange,
}: MediaFilterValueShapeAreaPercentageProps): JSX.Element => {
    const onDebounceSelectionChange = useDebouncedCallback((newValue: number) => {
        onSelectionChange(newValue);
    }, 500);

    return (
        <CustomNumberField
            isQuiet
            width={'100%'}
            isDisabled={isDisabled}
            value={Number(value)}
            onChange={onDebounceSelectionChange}
            step={0.01}
            maxValue={1}
            minValue={0}
            aria-label='media-filter-shape-area-percentage'
            formatOptions={{ style: 'percent' }}
        />
    );
};
