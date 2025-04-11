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

import { View } from '@adobe/react-spectrum';
import { SpectrumProgressCircleProps } from '@react-types/progress';

import { LoadingIndicator } from './loading-indicator.component';

import classes from './loading.module.scss';

interface LoadingProps extends Partial<SpectrumProgressCircleProps> {
    overlay?: boolean;
    id?: string;
}

export const Loading = ({ overlay = false, id, ...rest }: LoadingProps): JSX.Element => {
    return (
        <View
            height={'100%'}
            position={'absolute'}
            left={0}
            top={0}
            right={0}
            bottom={0}
            id={id}
            data-testid={id}
            UNSAFE_className={overlay ? classes.loadingBackground : ''}
        >
            <LoadingIndicator {...rest} />
        </View>
    );
};
