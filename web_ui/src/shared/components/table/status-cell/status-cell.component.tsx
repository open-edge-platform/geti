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

import { Flex, Text } from '@adobe/react-spectrum';

import { AcceptCircle, CrossCircle, HelpCircleSolidIcon, MinusCircle, Time } from '../../../../assets/icons';
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
