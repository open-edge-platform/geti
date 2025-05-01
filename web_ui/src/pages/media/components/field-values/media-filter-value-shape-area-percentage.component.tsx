// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CustomNumberField } from '@shared/components/configurable-parameters/cp-item/custom-number-field/custom-number-field.component';

import { SearchRuleValue } from '../../../../core/media/media-filter.interface';
import { useDebouncedCallback } from '../../../../hooks/use-debounced-callback/use-debounced-callback.hook';

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
