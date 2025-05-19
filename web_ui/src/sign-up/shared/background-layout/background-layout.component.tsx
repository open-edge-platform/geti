// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, ReactNode } from 'react';

import { View } from '@geti/ui';

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
