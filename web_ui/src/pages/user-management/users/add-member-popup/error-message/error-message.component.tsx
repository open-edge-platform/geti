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
