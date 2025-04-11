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

import { Heading, Text } from '@adobe/react-spectrum';

import { Unauthorized } from '../../../assets/images';
import { AccountStatus } from '../../../core/organizations/organizations.interface';
import { useHandleSignOut } from '../../../hooks/use-handle-sign-out/use-handle-sign-out.hook';
import { Button } from '../../../shared/components/button/button.component';
import { ErrorLayout } from '../error-layout/error-layout.component';

import classes from '../error-layout/error-layout.module.scss';

interface SuspendedOrganizationProps {
    status: AccountStatus.SUSPENDED | AccountStatus.DELETED;
}

export const SuspendedOrganization = ({ status }: SuspendedOrganizationProps): JSX.Element => {
    const handleSignOut = useHandleSignOut();

    return (
        <ErrorLayout>
            <Unauthorized />
            <Heading UNSAFE_className={classes.errorMessageHeader}>Account suspended</Heading>
            <Text UNSAFE_className={classes.errorMessage} UNSAFE_style={{ whiteSpace: 'break-spaces' }}>
                {`Your organization's account has been ${status.toLowerCase()}.
                Please contact your organization's administrator for more information.`}
            </Text>
            <Button variant={'accent'} onPress={handleSignOut} marginTop={'size-200'}>
                Logout
            </Button>
        </ErrorLayout>
    );
};
