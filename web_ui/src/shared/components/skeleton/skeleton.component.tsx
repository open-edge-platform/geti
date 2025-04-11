// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { View } from '@adobe/react-spectrum';
import { AriaLabelingProps, DOMProps, StyleProps } from '@react-types/shared';
import { clsx } from 'clsx';

import classes from './skeleton.module.scss';

interface SkeletonProps extends DOMProps, StyleProps, AriaLabelingProps {
    isCircle?: boolean;
    isAspectRatioOne?: boolean;
}

export const Skeleton = (props: SkeletonProps): JSX.Element => {
    const { isCircle, isAspectRatioOne = false, ...rest } = props;

    return (
        <View
            {...rest}
            UNSAFE_className={clsx(classes.skeleton, rest.UNSAFE_className, {
                [classes.circle]: isCircle,
                [classes.aspectRatio]: isAspectRatioOne,
            })}
        />
    );
};
