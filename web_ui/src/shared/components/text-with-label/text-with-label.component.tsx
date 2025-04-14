// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
