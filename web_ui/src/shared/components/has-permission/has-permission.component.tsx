// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useParams } from 'react-router-dom';

import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { useUsers } from '../../../core/users/hook/use-users.hook';
import { Resource, RESOURCE_TYPE } from '../../../core/users/users.interface';
import { useOrganizationIdentifier } from '../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { HasPermissionProps, OPERATION_NEW, OPERATION_OLD, UsePermissionType } from './has-permission.interface';
import { OPERATION_PERMISSION_NEW, OPERATION_PERMISSION_OLD } from './utils';

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

const usePermission = (): UsePermissionType => {
    const { FEATURE_FLAG_WORKSPACE_ACTIONS } = useFeatureFlags();
    const { useActiveUser } = useUsers();
    const { organizationId } = useOrganizationIdentifier();
    const { data: activeUser } = useActiveUser(organizationId);

    const verifyPermission = (
        operation: OPERATION_NEW | OPERATION_OLD,
        resources: Record<RESOURCE_TYPE, string | undefined>
    ): boolean => {
        const requiredPermissions = FEATURE_FLAG_WORKSPACE_ACTIONS
            ? OPERATION_PERMISSION_NEW[operation as OPERATION_NEW]
            : OPERATION_PERMISSION_OLD[operation as OPERATION_OLD];

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
    operations: (OPERATION_NEW | OPERATION_OLD)[],
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
    //debugger;
    const isPermitted = useCheckPermission(operations, resources, specialCondition);

    if (isPermitted) {
        return <>{children}</>;
    }

    return <>{Fallback}</>;
};
