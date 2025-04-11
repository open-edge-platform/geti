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

import { Content, Heading } from '@adobe/react-spectrum';
import CloudErrorIcon from '@spectrum-icons/workflow/CloudError';
import { useAuth } from 'react-oidc-context';

import { Button } from '../../../shared/components/button/button.component';
import { ErrorLayout } from '../error-layout/error-layout.component';

import classes from '../error-layout/error-layout.module.scss';

enum AuthError {
    USER_NOT_LOGGEDIN_ERROR = 'UserNotLoggedInError',
    USER_CANCELLED_ERROR = 'UserCancelledError',
}

const AuthErrorString: Record<AuthError, string> = {
    [AuthError.USER_NOT_LOGGEDIN_ERROR]: 'User is not currently logged in.',
    [AuthError.USER_CANCELLED_ERROR]: 'Login cancelled.',
};

const getErrorString = (error?: Error) => {
    if (!error) {
        return '';
    }

    const errorString = error.name as keyof typeof AuthErrorString;

    return AuthErrorString[errorString] || 'An error occurred during login.';
};

export const LoginErrorScreen = () => {
    const { error, signinRedirect } = useAuth();

    return (
        <ErrorLayout>
            <CloudErrorIcon size='XXL' />
            <Heading UNSAFE_className={classes.errorMessageHeader} data-testid={'login-error-id'}>
                Login error
            </Heading>
            <Content UNSAFE_className={classes.errorMessage}>{getErrorString(error)}</Content>
            <Button variant={'accent'} marginTop={'size-200'} onPress={() => signinRedirect()}>
                Try again
            </Button>
        </ErrorLayout>
    );
};
