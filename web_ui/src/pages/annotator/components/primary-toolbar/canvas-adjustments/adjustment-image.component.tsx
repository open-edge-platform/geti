// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Slider, View } from '@geti/ui';

import { AdjustmentHeader, AdjustmentHeaderProps } from './adjustment-header.component';

export const AdjustmentImage = ({
    headerText,
    value,
    handleValueChange,
    defaultValue,
    formatOptions,
}: AdjustmentHeaderProps): JSX.Element => {
    return (
        <View>
            <AdjustmentHeader
                headerText={headerText}
                value={value}
                defaultValue={defaultValue}
                formatOptions={formatOptions}
                handleValueChange={handleValueChange}
            />
            <Slider
                width={'100%'}
                step={1}
                value={value}
                minValue={-100}
                maxValue={100}
                onChange={handleValueChange}
                aria-label={`${headerText} adjustment`}
                fillOffset={0}
                isFilled
            />
        </View>
    );
};
