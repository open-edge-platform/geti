// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FC } from 'react';

import { Cell, Column, Row, TableBody, TableHeader, TableView } from '@adobe/react-spectrum';

import { paths } from '../../../core/services/routes';
import { TruncatedText } from '../../../shared/components/truncated-text/truncated-text.component';
import { User } from './mocked-user';
import { UserActions } from './user-actions/user-actions.component';

interface UsersTableProps {
    users: User[];
}

const COLUMNS = [
    {
        label: 'Users',
        isVisuallyHidden: false,
        isSortable: true,
    },
    {
        label: 'Email',
        isSortable: true,
        isVisuallyHidden: false,
    },
    {
        label: 'Actions',
        isSortable: false,
        isVisuallyHidden: true,
    },
];

export const UsersTable: FC<UsersTableProps> = ({ users }) => {
    return (
        <TableView aria-label={'Users table'} maxHeight={'100%'}>
            <TableHeader columns={COLUMNS}>
                {(column) => (
                    <Column key={column.label} allowsSorting={column.isSortable} hideHeader={column.isVisuallyHidden}>
                        {column.label.toLocaleUpperCase()}
                    </Column>
                )}
            </TableHeader>
            <TableBody items={users}>
                {(user) => (
                    <Row
                        key={user.id}
                        href={paths.intelAdmin.user.overview({ userId: user.id })}
                        routerOptions={{ viewTransition: true }}
                    >
                        <Cell textValue={`${user.firstName} ${user.secondName}`}>
                            <TruncatedText>{`${user.firstName} ${user.secondName}`}</TruncatedText>
                        </Cell>
                        <Cell textValue={user.email}>
                            <TruncatedText>{user.email}</TruncatedText>
                        </Cell>
                        <Cell>
                            <UserActions user={user} />
                        </Cell>
                    </Row>
                )}
            </TableBody>
        </TableView>
    );
};
