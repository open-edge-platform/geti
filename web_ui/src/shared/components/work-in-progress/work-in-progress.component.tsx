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

import { Flex, Heading, Text } from '@adobe/react-spectrum';

import { WorkInProgressIcon } from '../../../assets/images';

import classes from './work-in-progress.module.scss';

export const WorkInProgress = ({ description }: { description?: string }): JSX.Element => {
    return (
        <Flex direction='column' alignItems='center' justifyContent='center' height='100%'>
            <WorkInProgressIcon />
            <Heading level={1} UNSAFE_className={classes.heading}>
                Work in progress
            </Heading>
            <Text>{description ?? 'We are working hard to get this up and running'}</Text>
        </Flex>
    );
};
