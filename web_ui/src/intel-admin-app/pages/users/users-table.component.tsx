// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { paths } from '@geti/core/src/services/routes';
import { Cell, Column, Row, TableBody, TableHeader, TableView } from '@geti/ui';

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
