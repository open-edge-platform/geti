// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@adobe/react-spectrum';
import { StatusCell } from '@shared/components/table/status-cell/status-cell.component';

import { Email } from '../../../../../assets/icons';
import { User } from '../../../../../core/users/users.interface';
import { LastLoginCell } from '../../users-table/last-login-cell.component';

import classes from './user-summary.module.scss';

interface UserSummaryProps {
    user: User;
}
export const UserSummary = ({ user }: UserSummaryProps) => {
    return (
        <Flex
            alignItems='start'
            justifyContent='space-between'
            UNSAFE_className={classes.editMemberUserInfo}
            marginTop='size-160'
            marginBottom='size-115'
        >
            <Flex minWidth={0} alignItems='center' gap='size-130' UNSAFE_className={classes.editMemberEmail}>
                <Email id='email-icon' />
                <span id='user-email' data-testid={'user-email'} title={user.email} className={classes.editMemberEmail}>
                    {user.email}
                </span>
            </Flex>

            <Flex direction={'column'} alignItems={'end'}>
                <StatusCell id={`user-status-${user.firstName}-${user.lastName}`} status={user.status} />
                <Flex
                    gap={'size-50'}
                    UNSAFE_className={classes.lastLogin}
                    data-testid={`last-successful-login-${user.firstName}-${user.lastName}`}
                >
                    Last login:
                    <LastLoginCell
                        id={`last-successful-login-${user.firstName}-${user.lastName}`}
                        lastSuccessfulLogin={user.lastSuccessfulLogin}
                        direction='row'
                    />
                </Flex>
            </Flex>
        </Flex>
    );
};
