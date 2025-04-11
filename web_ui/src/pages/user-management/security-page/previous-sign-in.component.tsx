// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Text } from '@adobe/react-spectrum';

import { usePreviousSignIn } from '../../../shared/hooks/use-previous-sign-in.hook';

import classes from './security-page.module.scss';

export const PreviousSignIn = (): JSX.Element => {
    const { lastLoginDate } = usePreviousSignIn();

    if (!lastLoginDate) {
        return <></>;
    }

    return (
        <Flex width={'100%'} direction={'column'}>
            <Text>Previous sign-in</Text>
            <Text UNSAFE_className={classes.text}>{lastLoginDate}</Text>
        </Flex>
    );
};
