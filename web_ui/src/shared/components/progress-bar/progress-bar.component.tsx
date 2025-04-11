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

import { useEffect, useState } from 'react';

import { ProgressBar as SpectrumProgressBar } from '@adobe/react-spectrum';
import { SpectrumProgressBarProps } from '@react-types/progress';

interface ProgressBarProps extends SpectrumProgressBarProps {
    value: number;
    animationTime?: number;
}

export const ProgressBar = (props: ProgressBarProps): JSX.Element => {
    const { value, animationTime = 100 } = props;
    const [animatedValue, setAnimatedValue] = useState<number>(0);

    useEffect(() => {
        const id = setTimeout(() => {
            setAnimatedValue(value);
        }, animationTime);

        return () => clearTimeout(id);
    }, [animationTime, value]);

    return <SpectrumProgressBar {...props} value={animatedValue} />;
};
