// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { DimensionValue, Flex, ProgressCircle } from '@adobe/react-spectrum';
import { SpectrumProgressCircleProps } from '@react-types/progress';
import { Responsive } from '@react-types/shared/src/style';

interface LoadingIndicatorProps extends SpectrumProgressCircleProps {
    height?: Responsive<DimensionValue>;
}
export const LoadingIndicator = (props: LoadingIndicatorProps): JSX.Element => {
    const { size = 'L', height = '100%', ...rest } = props;

    return (
        <Flex alignItems={'center'} justifyContent={'center'} height={height}>
            <ProgressCircle aria-label={'Loading...'} isIndeterminate size={size} {...rest} />
        </Flex>
    );
};
