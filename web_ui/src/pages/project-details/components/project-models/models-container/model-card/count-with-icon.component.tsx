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

import { idMatchingFormat } from '../../../../../../test-utils/id-utils';

import classes from './model-card.module.scss';

interface CountWithIconProps {
    id: string;
    count: number;
    text: string;
    icon: ReactNode;
}

export const CountWithIcon = ({ id, icon, count, text }: CountWithIconProps): JSX.Element => {
    const message = count === 1 ? text : text + 's';

    return (
        <Flex alignItems={'center'} gap={'size-50'} UNSAFE_className={classes.countWithIcon}>
            {icon}
            <Text
                id={`${idMatchingFormat(text)}-count--${id}-id`}
                data-testid={`${idMatchingFormat(text)}-count-${id}-id`}
            >{`${count} ${message}`}</Text>
        </Flex>
    );
};
