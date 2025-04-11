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

import { Slider, View } from '@adobe/react-spectrum';

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
