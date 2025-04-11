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
