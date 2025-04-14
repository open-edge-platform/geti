// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
