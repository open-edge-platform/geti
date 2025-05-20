// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Heading, Link } from '@geti/ui';
import CloudErrorIcon from '@spectrum-icons/workflow/CloudError';

import { paths } from '../../../core/services/routes';
import { redirectTo } from '../../../shared/utils';

import classes from '../error-layout/error-layout.module.scss';

interface ErrorScreenProps {
    errorMessage: string;
    resetErrorBoundary: (...args: unknown[]) => void;
}

export const ErrorScreen = ({ errorMessage, resetErrorBoundary }: ErrorScreenProps): JSX.Element => {
    return (
        <>
            <CloudErrorIcon size='XXL' />
            <Heading UNSAFE_className={classes.errorMessageHeader}>An error occurred...</Heading>
            <Heading UNSAFE_className={classes.errorMessage}>
                Please try{' '}
                <Link
                    variant='overBackground'
                    onPress={() => {
                        // hard refresh
                        redirectTo(window.location.href);
                    }}
                >
                    refreshing
                </Link>{' '}
                the page or going{' '}
                <Link variant='overBackground' onPress={resetErrorBoundary}>
                    back
                </Link>{' '}
                to the previous screen.
            </Heading>
            <Heading UNSAFE_className={classes.errorMessage}>
                <Link variant='overBackground' onPress={() => redirectTo(paths.root({}))}>
                    Go back to home
                </Link>
            </Heading>
            {errorMessage && (
                <Heading id='error-description' UNSAFE_className={classes.errorMessage}>
                    Error: {errorMessage}
                </Heading>
            )}
        </>
    );
};
