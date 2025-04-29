// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
