// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ComboBox, Item } from '@adobe/react-spectrum';

import { SearchRuleValue } from '../../../../core/media/media-filter.interface';
import { useUsers } from '../../../../core/users/hook/use-users.hook';
import { RESOURCE_TYPE } from '../../../../core/users/users.interface';
import { useOrganizationIdentifier } from '../../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { runWhenTruthy } from '../../../../shared/utils';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';

interface MediaFilterValueUsersListProps {
    value: SearchRuleValue;
    onSelectionChange: (key: SearchRuleValue) => void;
}

export const MediaFilterValueUsersList = ({
    value,
    onSelectionChange,
}: MediaFilterValueUsersListProps): JSX.Element => {
    const { organizationId } = useOrganizationIdentifier();
    const { useGetUsersQuery } = useUsers();
    const { project } = useProject();
    const { users, isLoading, isError } = useGetUsersQuery(organizationId, {
        resourceType: RESOURCE_TYPE.PROJECT,
        resourceId: project.id,
    });

    const handleSelectionChange = runWhenTruthy(onSelectionChange);

    return (
        <ComboBox
            isQuiet
            defaultItems={users ?? []}
            loadingState={isLoading ? 'loading' : 'idle'}
            id='media-filter-users-list'
            aria-label='media-filter-users-list'
            isDisabled={isError}
            selectedKey={value as string}
            onSelectionChange={handleSelectionChange}
        >
            {({ firstName, lastName, id }) => {
                const fullName = `${firstName} ${lastName}`;

                return <Item key={id}>{fullName}</Item>;
            }}
        </ComboBox>
    );
};
