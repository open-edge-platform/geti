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

import { useParams } from 'react-router-dom';

import { useUsers } from '../../../core/users/hook/use-users.hook';
import { Resource, RESOURCE_TYPE } from '../../../core/users/users.interface';
import { useOrganizationIdentifier } from '../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { HasPermissionProps, OPERATION, UsePermissionType } from './has-permission.interface';
import { OPERATION_PERMISSION } from './utils';

const useResource = (selectedResources?: Resource[]): Record<RESOURCE_TYPE, string | undefined> => {
    const params = useParams<{ organizationId?: string; workspaceId?: string; projectId?: string }>();

    return {
        [RESOURCE_TYPE.ORGANIZATION]:
            params?.organizationId ?? selectedResources?.find(({ type }) => type === RESOURCE_TYPE.ORGANIZATION)?.id,
        [RESOURCE_TYPE.WORKSPACE]:
            params?.workspaceId ?? selectedResources?.find(({ type }) => type === RESOURCE_TYPE.WORKSPACE)?.id,
        [RESOURCE_TYPE.PROJECT]:
            params?.projectId ?? selectedResources?.find(({ type }) => type === RESOURCE_TYPE.PROJECT)?.id,
    };
};

export const usePermission = (): UsePermissionType => {
    const { useActiveUser } = useUsers();
    const { organizationId } = useOrganizationIdentifier();
    const { data: activeUser } = useActiveUser(organizationId);

    const verifyPermission = (operation: OPERATION, resources: Record<RESOURCE_TYPE, string | undefined>): boolean => {
        const requiredPermissions = OPERATION_PERMISSION[operation];

        return (
            activeUser?.roles.some((userRole) =>
                requiredPermissions.some((permission) => {
                    const resourceId = resources[permission.resourceType as RESOURCE_TYPE];
                    const isResourceIdEqual = resourceId === userRole.resourceId;

                    return (
                        permission.role === userRole.role &&
                        permission.resourceType === userRole.resourceType &&
                        isResourceIdEqual
                    );
                })
            ) ?? false
        );
    };

    return {
        verifyPermission,
    };
};

export const useCheckPermission = (
    operations: OPERATION[],
    selectedResources?: Resource[],
    specialCondition = false
) => {
    const { verifyPermission } = usePermission();
    const resources = useResource(selectedResources);

    return operations.every((operation) => verifyPermission(operation, resources)) || specialCondition;
};

export const HasPermission = ({
    children,
    operations,
    resources,
    Fallback = <></>,
    specialCondition = false,
}: HasPermissionProps): JSX.Element => {
    const isPermitted = useCheckPermission(operations, resources, specialCondition);

    if (isPermitted) {
        return <>{children}</>;
    }

    return <>{Fallback}</>;
};
