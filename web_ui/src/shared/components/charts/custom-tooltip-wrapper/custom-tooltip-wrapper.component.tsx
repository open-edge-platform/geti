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

import { ReactNode } from 'react';

import { View } from '@react-spectrum/view';

import classes from './custom-tooltip-wrapper.module.scss';

interface CustomTooltipWrapperProps {
    children: ReactNode;
}

export const CustomTooltipWrapper = ({ children }: CustomTooltipWrapperProps): JSX.Element => {
    return <View UNSAFE_className={classes.customTooltipWrapper}>{children}</View>;
};
