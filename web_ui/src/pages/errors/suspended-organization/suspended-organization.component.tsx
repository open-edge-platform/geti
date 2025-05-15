// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Heading, Text } from '@adobe/react-spectrum';
import { Button } from '@geti/ui';

import { Unauthorized } from '../../../assets/images';
import { AccountStatus } from '../../../core/organizations/organizations.interface';
import { useHandleSignOut } from '../../../hooks/use-handle-sign-out/use-handle-sign-out.hook';
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
