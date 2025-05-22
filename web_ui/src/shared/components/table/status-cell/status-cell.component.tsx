// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text } from '@geti/ui';
import { AcceptCircle, CrossCircle, HelpCircleSolidIcon, MinusCircle, Time } from '@geti/ui/icons';

import { AccountStatus } from '../../../../core/organizations/organizations.interface';

import classes from './status-cell.module.scss';

interface StatusCellProps<T extends AccountStatus> {
    id?: string;
    status: T;
}

const STATUS_ICON: Record<AccountStatus, JSX.Element> = {
    [AccountStatus.ACTIVATED]: <AcceptCircle className={classes.activatedStatus} />,
    [AccountStatus.INVITED]: <Time className={classes.registeredStatus} />,
    [AccountStatus.SUSPENDED]: <MinusCircle className={classes.suspendedStatus} />,
    [AccountStatus.DELETED]: <CrossCircle className={classes.deletedStatus} />,
    [AccountStatus.REQUESTED_ACCESS]: <HelpCircleSolidIcon />,
};

export const StatusCell = <T extends AccountStatus>({ id, status }: StatusCellProps<T>): JSX.Element => {
    return (
        <Flex id={id} alignItems={'center'} gap={'size-50'}>
            {STATUS_ICON[status]}
            <Text>{status}</Text>
        </Flex>
    );
};
