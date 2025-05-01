// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Cell, Column, Row, TableBody, TableHeader, TableView } from '@adobe/react-spectrum';
import { DateCell } from '@shared/components/table/date-cell/date-cell.component';
import { StatusCell } from '@shared/components/table/status-cell/status-cell.component';

import { USER_ROLE } from '../../../core/users/users.interface';
import { OrganizationNameCell } from '../organizations/cells/organization-name-cell.component';
import { User } from '../users/mocked-user';
import { MembershipActions } from './membership-actions/membership-actions.component';
import { Membership } from './mocked-memberships';

const COLUMNS = [
    {
        label: 'Organization',
        isVisuallyHidden: false,
        isSortable: true,
    },
    {
        label: 'Role',
        isVisuallyHidden: false,
        isSortable: false,
    },
    {
        label: 'Status',
        isVisuallyHidden: false,
        isSortable: true,
    },
    {
        label: 'Membership since',
        isVisuallyHidden: false,
        isSortable: true,
    },
    {
        label: 'Actions',
        isVisuallyHidden: true,
        isSortable: false,
    },
];

interface MembershipsTableProps {
    user: User;
    memberships: Membership[];
}

const ROLE_MAPPER = {
    [USER_ROLE.ORGANIZATION_CONTRIBUTOR]: 'Contributor',
    [USER_ROLE.ORGANIZATION_ADMIN]: 'Admin',
} as const;

export const MembershipsTable: FC<MembershipsTableProps> = ({ user, memberships }) => {
    return (
        <TableView aria-label={'Memberships table'} maxHeight={'100%'}>
            <TableHeader columns={COLUMNS}>
                {(column) => (
                    <Column key={column.label} allowsSorting={column.isSortable} hideHeader={column.isVisuallyHidden}>
                        {column.label.toLocaleUpperCase()}
                    </Column>
                )}
            </TableHeader>
            <TableBody items={memberships}>
                {(membership) => (
                    <Row key={membership.id}>
                        <Cell textValue={membership.organizationName}>
                            <OrganizationNameCell id={membership.organizationId} name={membership.organizationName} />
                        </Cell>
                        <Cell textValue={membership.role}>{ROLE_MAPPER[membership.role]}</Cell>
                        <Cell textValue={membership.status}>
                            <StatusCell status={membership.status} />
                        </Cell>
                        <Cell textValue={membership.createdAt}>
                            <DateCell date={membership.createdAt} direction={'row'} />
                        </Cell>
                        <Cell>
                            <MembershipActions membership={membership} user={user} />
                        </Cell>
                    </Row>
                )}
            </TableBody>
        </TableView>
    );
};
