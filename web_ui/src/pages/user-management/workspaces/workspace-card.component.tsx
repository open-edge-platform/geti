// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';
import { RESOURCE_TYPE } from '@geti/core/src/users/users.interface';
import { WorkspaceEntity } from '@geti/core/src/workspaces/services/workspaces.interface';
import { Button, CornerIndicator, Divider, Flex, Heading, View } from '@geti/ui';
import { useNavigate } from 'react-router-dom';

import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { ActionMenu } from '../../../shared/components/action-menu/action-menu.component';
import { DeleteDialog } from '../../../shared/components/delete-dialog/delete-dialog.component';
import { EditNameDialog } from '../../../shared/components/edit-name-dialog/edit-name-dialog.component';
import { HasPermission } from '../../../shared/components/has-permission/has-permission.component';
import { OPERATION } from '../../../shared/components/has-permission/has-permission.interface';
import { useWorkspaceActions } from '../../landing-page/workspaces-tabs/use-workspace-actions.hook';
import { WorkspaceMenuActions } from '../../landing-page/workspaces-tabs/utils';
import { MAX_LENGTH_OF_WORKSPACE_NAME, MIN_LENGTH_OF_WORKSPACE_NAME } from './utils';

interface WorkspaceCardProps {
    workspace: WorkspaceEntity;
    workspaces: WorkspaceEntity[];
    isDefaultWorkspace: boolean;
}

export const WorkspaceCard = ({ workspace, workspaces, isDefaultWorkspace }: WorkspaceCardProps): JSX.Element => {
    const navigate = useNavigate();
    const { getAvailableItems, handleMenuAction, deleteDialog, editDialog } = useWorkspaceActions(workspaces.length);
    const { FEATURE_FLAG_WORKSPACE_ACTIONS } = useFeatureFlags();

    const workspaceActions = getAvailableItems(isDefaultWorkspace).map((item) => ({
        name: item,
        id: item,
    }));
    const handleSeeMore = (): void => {
        navigate(paths.workspace({ organizationId: workspace.organizationId, workspaceId: workspace.id }));
    };

    const handleEditDialog = (newName: string): void => {
        editDialog.editWorkspaceMutation.mutate(
            { ...workspace, name: newName },
            {
                onSuccess: () => {
                    editDialog.editWorkspaceDialogState.close();
                },
            }
        );
    };

    const handleDeleteWorkspace = (): void => {
        deleteDialog.deleteWorkspaceMutation.mutate(
            { id: workspace.id },
            {
                onSuccess: () => {
                    deleteDialog.deleteWorkspaceDialogState.close();
                },
            }
        );
    };

    return (
        <View borderWidth={'thin'} borderColor={'gray-200'} paddingY={'size-100'} paddingX={'size-200'} height={'100%'}>
            <CornerIndicator
                testId={`${workspace.name}-default-workspace-indicator`}
                isActive={FEATURE_FLAG_WORKSPACE_ACTIONS && isDefaultWorkspace}
            >
                <Heading margin={0}>{workspace.name}</Heading>
            </CornerIndicator>
            <Divider size={'S'} marginY={'size-150'} />
            <Flex justifyContent={'space-between'}>
                <Button
                    data-testid={`workspace-${workspace.id}-see-more-button-id`}
                    variant={'primary'}
                    onPress={handleSeeMore}
                >
                    See more
                </Button>
                <HasPermission
                    operations={[OPERATION.WORKSPACE_MANAGEMENT]}
                    resources={[{ type: RESOURCE_TYPE.WORKSPACE, id: workspace.id }]}
                >
                    <ActionMenu<WorkspaceMenuActions>
                        items={workspaceActions}
                        id={`${workspace.name}-action-menu`}
                        onAction={(key) => handleMenuAction(key, workspace.id)}
                    />
                </HasPermission>
            </Flex>

            <HasPermission
                operations={[OPERATION.WORKSPACE_MANAGEMENT]}
                resources={[{ type: RESOURCE_TYPE.WORKSPACE, id: workspace.id }]}
            >
                <DeleteDialog
                    name={workspace.name}
                    title={'workspace'}
                    onAction={handleDeleteWorkspace}
                    triggerState={deleteDialog.deleteWorkspaceDialogState}
                />
                <EditNameDialog
                    isLoading={editDialog.editWorkspaceMutation.isPending}
                    triggerState={editDialog.editWorkspaceDialogState}
                    onAction={handleEditDialog}
                    defaultName={workspace.name}
                    names={workspaces.map(({ name }) => name).filter((name) => name !== workspace.name)}
                    title={'workspace name'}
                    nameLimitations={{
                        maxLength: MAX_LENGTH_OF_WORKSPACE_NAME,
                        minLength: MIN_LENGTH_OF_WORKSPACE_NAME,
                    }}
                />
            </HasPermission>
        </View>
    );
};
