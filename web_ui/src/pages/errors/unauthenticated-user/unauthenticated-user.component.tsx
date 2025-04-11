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

import { useEffect } from 'react';

import { Heading, Text } from '@adobe/react-spectrum';

import { Unauthorized } from '../../../assets/images';
import { paths } from '../../../core/services/routes';
import { Button } from '../../../shared/components/button/button.component';
import { redirectTo } from '../../../shared/utils';

import classes from '../error-layout/error-layout.module.scss';

export const UnauthenticatedUser = (): JSX.Element => {
    useEffect(() => {
        // For privacy reasons we cannot show the app name as document title for unauthenticated users
        const previousHtmlTitle = document.title;

        document.title = 'Unauthenticated';

        return () => {
            document.title = previousHtmlTitle;
        };
    }, []);

    const handleOnPress = (): void => {
        redirectTo(paths.root({}));
    };

    return (
        <>
            <Unauthorized />
            <Heading UNSAFE_className={classes.errorMessageHeader}>Unauthenticated</Heading>
            <Text UNSAFE_className={classes.errorMessage}>
                Session expired, you probably have logged on other device.
            </Text>
            <Button variant={'accent'} onPress={handleOnPress} marginTop={'size-200'}>
                Sign in
            </Button>
        </>
    );
};
