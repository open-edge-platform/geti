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

import { Content, Flex, Heading } from '@adobe/react-spectrum';
import { useQueryErrorResetBoundary } from '@tanstack/react-query';

import { AccessDenied } from '../../../assets/images';
import { useHandleSignOut } from '../../../hooks/use-handle-sign-out/use-handle-sign-out.hook';
import { Button } from '../../../shared/components/button/button.component';
import { CustomerSupportLink } from '../../../shared/components/customer-support-link/customer-support-link.component';
import { openNewTab } from '../../../shared/utils';
import { ErrorLayout } from '../error-layout/error-layout.component';

import classes from '../error-layout/error-layout.module.scss';

export const InvalidOrganizationsScreen = () => {
    const signout = useHandleSignOut();
    const { reset } = useQueryErrorResetBoundary();

    const handleSignOut = () => {
        reset();
        signout();
    };

    return (
        <ErrorLayout>
            <AccessDenied />
            <Heading UNSAFE_className={classes.errorMessageHeader} data-testid={'access-denied-id'}>
                Access denied
            </Heading>
            <Content UNSAFE_className={classes.errorMessage}>
                You do not have access to any Intel Geti organization. Please contact your organization admin to invite
                you to the system, request a trial, or contact <CustomerSupportLink /> if you already received an
                invitation.
            </Content>
            <Flex gap='size-200' marginTop={'size-300'}>
                <Button
                    variant={'accent'}
                    href='https://geti.intel.com/request-trial'
                    onPress={() => {
                        openNewTab('https://geti.intel.com/request-trial');
                        reset();
                    }}
                >
                    Request trial
                </Button>
                <Button variant={'secondary'} onPress={handleSignOut}>
                    Logout
                </Button>
            </Flex>
        </ErrorLayout>
    );
};
