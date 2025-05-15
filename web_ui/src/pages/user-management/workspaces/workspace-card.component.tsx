// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex, Heading, View } from '@adobe/react-spectrum';
import { Button } from '@geti/ui';
import { useNavigate } from 'react-router-dom';

import { paths } from '../../../core/services/routes';
import { RESOURCE_TYPE } from '../../../core/users/users.interface';
import { WorkspaceEntity } from '../../../core/workspaces/services/workspaces.interface';
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
}

export const WorkspaceCard = ({ workspace, workspaces }: WorkspaceCardProps): JSX.Element => {
    const navigate = useNavigate();
    const { items, handleMenuAction, deleteDialog, editDialog } = useWorkspaceActions(workspaces.length);

    const workspaceActions = items.map((item) => ({ name: item, id: item }));
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
            <Heading margin={0}>{workspace.name}</Heading>
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
                        onAction={handleMenuAction}
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
