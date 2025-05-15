// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Content, Heading } from '@adobe/react-spectrum';
import { Button } from '@geti/ui';
import CloudErrorIcon from '@spectrum-icons/workflow/CloudError';
import { useAuth } from 'react-oidc-context';

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
