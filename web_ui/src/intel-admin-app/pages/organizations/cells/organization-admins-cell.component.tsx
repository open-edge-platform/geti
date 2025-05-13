// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Fragment } from 'react';

import { Flex, Text } from '@adobe/react-spectrum';
import { isEmpty } from 'lodash-es';

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
