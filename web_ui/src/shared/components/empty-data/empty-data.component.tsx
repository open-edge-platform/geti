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

import { ReactNode } from 'react';

import { Flex, Text } from '@adobe/react-spectrum';

import classes from './empty-data.module.scss';

interface EmptyDataProps {
    title: string;
    text: string;
    beforeText?: ReactNode;
    afterText?: ReactNode;
}

export const EmptyData = ({ title, text, beforeText = null, afterText = null }: EmptyDataProps): JSX.Element => {
    return (
        <Flex justifyContent={'center'} alignItems={'center'} height={'100%'} id='empty-data-id'>
            <Flex direction={'column'} alignItems={'center'}>
                {beforeText}

                <Text marginTop={'size-150'} UNSAFE_className={classes.emptyData}>
                    {title}
                </Text>
                <Text>{text}</Text>

                {afterText}
            </Flex>
        </Flex>
    );
};
