// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps } from 'react';

import { DimensionValue } from '@adobe/react-spectrum';
import { Text } from '@react-spectrum/text';

import classes from './error-message.module.scss';

interface ErrorMessageProps extends Omit<ComponentProps<typeof Text>, 'children'> {
    message: string;
    id: string;
    paddingLeft?: DimensionValue;
}

export const ErrorMessage = (props: ErrorMessageProps): JSX.Element => {
    const { message, id, UNSAFE_style, ...rest } = props;

    return message ? (
        <Text
            UNSAFE_className={classes.errorMessage}
            id={`${id}-error-msg`}
            UNSAFE_style={{
                paddingLeft: props.paddingLeft || 'size-125',
                ...UNSAFE_style,
            }}
            {...rest}
        >
            {message}
        </Text>
    ) : (
        <></>
    );
};
