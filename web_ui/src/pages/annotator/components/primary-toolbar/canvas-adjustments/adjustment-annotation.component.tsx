// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Slider, View } from '@geti/ui';

import { AdjustmentHeader, AdjustmentHeaderProps } from './adjustment-header.component';

interface AdjustmentAnnotationProps extends AdjustmentHeaderProps {
    isDisabled?: boolean;
}

export const AdjustmentAnnotation = ({
    headerText,
    value,
    handleValueChange,
    formatOptions,
    defaultValue,
    isDisabled,
}: AdjustmentAnnotationProps): JSX.Element => {
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
                minValue={0}
                maxValue={1}
                step={0.01}
                value={value}
                onChange={handleValueChange}
                aria-label={`${headerText} adjustment`}
                isDisabled={isDisabled}
                isFilled
            />
        </View>
    );
};
