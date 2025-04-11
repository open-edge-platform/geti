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

import { USER_ROLE } from '../../../core/users/users.interface';
import { DateCell } from '../../../shared/components/table/date-cell/date-cell.component';
import { StatusCell } from '../../../shared/components/table/status-cell/status-cell.component';
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
