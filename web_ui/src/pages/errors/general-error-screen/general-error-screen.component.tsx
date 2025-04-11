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

import { Heading, Link } from '@adobe/react-spectrum';
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
