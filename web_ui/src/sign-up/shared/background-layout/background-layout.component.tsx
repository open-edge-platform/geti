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

import { ComponentProps, ReactNode } from 'react';

import { View } from '@adobe/react-spectrum';

import { Header } from '../header/header.component';

import classes from './background-layout.module.scss';

interface BackgroundLayoutProps {
    children: ReactNode;
    height?: ComponentProps<typeof View>['height'];
    className?: ComponentProps<typeof View>['UNSAFE_className'];
}

export const BackgroundLayout = ({ children, height, className }: BackgroundLayoutProps): JSX.Element => (
    <View UNSAFE_className={classes.backgroundLayout} minHeight={'100vh'} height={'100%'}>
        <View
            backgroundColor={'gray-50'}
            width={'52rem'}
            height={height}
            UNSAFE_className={classes.layoutContainer}
            position={'relative'}
        >
            <Header />
            <View paddingX={'size-600'} paddingY={'size-400'} UNSAFE_className={className}>
                {children}
            </View>
        </View>
    </View>
);
