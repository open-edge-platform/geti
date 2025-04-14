// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, ReactNode } from 'react';

import { View } from '@adobe/react-spectrum';

import classes from './indicator-wrapper.module.scss';

interface IndicatorProps extends ComponentProps<typeof View> {
    children: ReactNode;
}

export const IndicatorWrapper = ({
    children,
    UNSAFE_className: customClasses = '',
    ...rest
}: IndicatorProps): JSX.Element => {
    return (
        <View
            zIndex={1}
            padding={'size-50'}
            position={'absolute'}
            borderRadius={'small'}
            UNSAFE_className={[classes.indicatorWrapper, customClasses].join(' ')}
            height={'size-200'}
            {...rest}
        >
            {children}
        </View>
    );
};
