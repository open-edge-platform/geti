// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ReactNode } from 'react';

import { Text, View, ViewProps } from '@adobe/react-spectrum';
import { ColorVersion } from '@react-types/shared';

import classes from './text-with-label.module.scss';

interface TextWithLabelProps<C extends ColorVersion> extends ViewProps<C> {
    children: ReactNode;
    label: string;
}

export const TextWithLabel = <C extends ColorVersion>(props: TextWithLabelProps<C>): JSX.Element => {
    const { children, label, ...rest } = props;

    return (
        <View {...rest}>
            <Text UNSAFE_className={classes.label}>{label}</Text>
            <br />
            <Text UNSAFE_className={classes.text}>{children}</Text>
        </View>
    );
};
