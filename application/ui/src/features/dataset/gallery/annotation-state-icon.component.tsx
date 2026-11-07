// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { View } from '@geti-ui/ui';
import { CheckCircleOutlined, Search } from '@geti-ui/ui/icons';

import classes from './annotation-state-icon.module.scss';

type AnnotationStatusIconProps = {
    isAnnotated: boolean;
};

export const AnnotationStatusIcon = ({ isAnnotated }: AnnotationStatusIconProps) => {
    if (isAnnotated) {
        return (
            <View UNSAFE_className={classes.annotated}>
                <CheckCircleOutlined role='img' aria-label='Annotated' />
            </View>
        );
    }

    return (
        <View UNSAFE_className={classes.notAnnotated}>
            <Search role='img' aria-label='Not annotated' />
        </View>
    );
};
