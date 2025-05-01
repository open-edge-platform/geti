// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComboBox, Item } from '@adobe/react-spectrum';
import { runWhenTruthy } from '@shared/utils';

import { SearchRuleValue } from '../../../../core/media/media-filter.interface';
import { useUsers } from '../../../../core/users/hook/use-users.hook';
import { RESOURCE_TYPE } from '../../../../core/users/users.interface';
import { useOrganizationIdentifier } from '../../../../hooks/use-organization-identifier/use-organization-identifier.hook';
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
