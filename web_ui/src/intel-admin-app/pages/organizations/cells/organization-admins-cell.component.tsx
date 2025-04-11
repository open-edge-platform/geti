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

import { Fragment } from 'react';

import { Flex, Text } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

import { OrganizationAdmin } from '../../../../core/organizations/dtos/organizations.interface';
import { Organization } from '../../../../core/organizations/organizations.interface';
import { CasualCell } from '../../../../shared/components/table/components/casual-cell/casual-cell.component';
import { TableCellProps } from '../../../../shared/components/table/table.interface';
import { OrganizationAdminsCopyText } from './organization-admins-copy-text.component';

const getDisplayName = (admin: OrganizationAdmin) => {
    if (isEmpty(admin.firstName) || isEmpty(admin.lastName)) {
        return admin.email;
    } else {
        return `${admin.firstName} ${admin.lastName}`;
    }
};

export const OrganizationAdminsCell = (props: TableCellProps): JSX.Element => {
    const organization = props.rowData as Organization;

    if (isEmpty(organization.admins)) {
        return <></>;
    }

    return (
        <Flex gap='size-50' data-testid={`organization-${organization.name}-admins-cell-content`}>
            {organization.admins.map((admin, index) => {
                const adminName = getDisplayName(admin);
                const newProps = {
                    ...props,
                    cellData: adminName,
                };

                return (
                    <Fragment key={adminName}>
                        {!!index ? <Text>,</Text> : <></>}
                        <CasualCell
                            {...newProps}
                            tooltip={
                                <OrganizationAdminsCopyText
                                    text={admin.email}
                                    aria-label={'Copy email'}
                                    data-testid={`copy-email-${admin.email}`}
                                    confirmationMessage={'Email copied successfully'}
                                />
                            }
                        />
                    </Fragment>
                );
            })}
        </Flex>
    );
};
