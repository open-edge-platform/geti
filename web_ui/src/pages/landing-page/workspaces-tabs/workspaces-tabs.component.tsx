// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import {
    ActionButton,
    Flex,
    Item,
    LoadingIndicator,
    TabList,
    TabPanels,
    Tabs,
    Tooltip,
    TooltipTrigger,
} from '@geti/ui';
import { useNavigate } from 'react-router-dom';

import { Add } from '../../../assets/icons';
import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { paths } from '../../../core/services/routes';
import { useWorkspacesApi } from '../../../core/workspaces/hooks/use-workspaces.hook';
import { useOrganizationIdentifier } from '../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { usePinnedCollapsedItems } from '../../../hooks/use-pinned-collapsed-items/use-pinned-collapsed-items.hook';
import { PinnedCollapsedItemsAction } from '../../../hooks/use-pinned-collapsed-items/use-pinned-collapsed-items.interface';
import { useWorkspaces } from '../../../providers/workspaces-provider/workspaces-provider.component';
import { CollapsedItemsPicker } from '../../../shared/components/collapsed-items-picker/collapsed-items-picker.component';
import { CustomTabItemWithMenu } from '../../../shared/components/custom-tab-item/custom-tab-item-with-menu.component';
import { CustomTabItem } from '../../../shared/components/custom-tab-item/custom-tab-item.component';
import { DeleteDialog } from '../../../shared/components/delete-dialog/delete-dialog.component';
import { EditNameDialog } from '../../../shared/components/edit-name-dialog/edit-name-dialog.component';
import { HasPermission } from '../../../shared/components/has-permission/has-permission.component';
import { OPERATION } from '../../../shared/components/has-permission/has-permission.interface';
import { TabItem } from '../../../shared/components/tabs/tabs.interface';
import { getUniqueNameFromArray, hasEqualId } from '../../../shared/utils';
import { MAX_LENGTH_OF_WORKSPACE_NAME, MIN_LENGTH_OF_WORKSPACE_NAME } from '../../user-management/workspaces/utils';
import { LandingPageWorkspace as Workspace } from '../landing-page-workspace/landing-page-workspace.component';
import { useWorkspaceActions } from './use-workspace-actions.hook';

import classes from '../../../shared/components/custom-tab-item/custom-tab-item.module.scss';

const MAX_NUMBER_OF_DISPLAYED_WORKSPACES = 6;

const usePinnedCollapsedWorkspaces = () => {
    const navigate = useNavigate();
    const { organizationId } = useOrganizationIdentifier();

    const { workspaces, workspaceId: selectedWorkspaceId } = useWorkspaces();
    const [pinnedWorkspaces, collapsedWorkspaces, dispatch] = usePinnedCollapsedItems(
        workspaces,
        selectedWorkspaceId,
        MAX_NUMBER_OF_DISPLAYED_WORKSPACES
    );

    const selectWorkspace = (workspaceId: string) => {
        navigate(paths.workspace({ organizationId, workspaceId }));
    };

    const handleSelectWorkspace = (key: Key): void => {
        if (key === selectedWorkspaceId) {
            return;
        }

        selectWorkspace(String(key));
    };

    const handleSelectWorkspaceFromCollapsed = (key: Key): void => {
        const newSelectedWorkspaceId = String(key);

        dispatch({ type: PinnedCollapsedItemsAction.SWAP, payload: { id: newSelectedWorkspaceId } });

        selectWorkspace(newSelectedWorkspaceId);
    };

    return {
        workspaces,
        selectWorkspace,
        dispatchWorkspaces: dispatch,
        pinnedWorkspaces,
        collapsedWorkspaces,
        handleSelectWorkspace,
        handleSelectWorkspaceFromCollapsed,
        selectedWorkspaceId,
    };
};

export const WorkspacesTabs = (): JSX.Element => {
    const { organizationId } = useOrganizationIdentifier();
    const {
        workspaces,
        selectWorkspace,
        dispatchWorkspaces,
        selectedWorkspaceId,
        collapsedWorkspaces,
        pinnedWorkspaces,
        handleSelectWorkspace,
    } = usePinnedCollapsedWorkspaces();
    const { FEATURE_FLAG_WORKSPACE_ACTIONS } = useFeatureFlags();
    const numberOfWorkspaces = pinnedWorkspaces.length + collapsedWorkspaces.length;

    const { items, handleMenuAction, deleteDialog, editDialog } = useWorkspaceActions(numberOfWorkspaces);
    const { useCreateWorkspaceMutation } = useWorkspacesApi(organizationId);
    const createWorkspace = useCreateWorkspaceMutation();

    const workspacesNames = workspaces.map(({ name }) => name);

    const hasSelectedPinnedItem = pinnedWorkspaces.find(hasEqualId(selectedWorkspaceId)) !== undefined;

    const pinnedItems: TabItem[] = pinnedWorkspaces.map(({ id, name }) => ({
        name,
        id: `${id === selectedWorkspaceId ? 'selected-' : ''}workspace-${id}`,
        key: id,
        children: <Workspace />,
    }));

    const collapsedItems = collapsedWorkspaces.map(({ id, name }) => ({ id, name }));

    const handleEditDialog = (newName: string): void => {
        const workspace = workspaces.find(hasEqualId(selectedWorkspaceId));

        if (workspace === undefined) {
            return;
        }

        editDialog.editWorkspaceMutation.mutate(
            { ...workspace, name: newName },
            {
                onSuccess: () => {
                    dispatchWorkspaces({
                        type: PinnedCollapsedItemsAction.UPDATE,
                        payload: { id: workspace.id, name: newName },
                    });

                    editDialog.editWorkspaceDialogState.close();
                },
            }
        );
    };

    const handleDeleteWorkspace = (): void => {
        const id = selectedWorkspaceId;

        deleteDialog.deleteWorkspaceMutation.mutate(
            { id },
            {
                onSuccess: () => {
                    selectWorkspace(workspaces[0].id);

                    dispatchWorkspaces({
                        type: PinnedCollapsedItemsAction.REMOVE,
                        payload: { id },
                    });

                    deleteDialog.deleteWorkspaceDialogState.close();
                },
            }
        );
    };

    const handleCreateWorkspace = (): void => {
        const uniqueName = getUniqueNameFromArray(
            workspaces.map(({ name }) => name),
            'Workspace '
        );

        createWorkspace.mutate(
            { name: uniqueName },
            {
                onSuccess: (workspace) => {
                    dispatchWorkspaces({ type: PinnedCollapsedItemsAction.CREATE, payload: workspace });

                    selectWorkspace(workspace.id);
                },
            }
        );
    };

    return (
        <Flex id={`page-layout-id`} direction='column' height='100%' UNSAFE_className={classes.componentWrapper}>
            <Tabs
                selectedKey={selectedWorkspaceId}
                items={pinnedItems}
                aria-label={'Workspaces tabs'}
                height={'100%'}
                width={'100%'}
                orientation={'vertical'}
                onSelectionChange={handleSelectWorkspace}
            >
                <Flex width={'100%'} alignItems={'end'} UNSAFE_className={classes.tabWrapper}>
                    <TabList UNSAFE_className={classes.tabList}>
                        {(item: TabItem) => (
                            <Item textValue={item.name as string} key={item.key}>
                                <>
                                    <Flex alignItems={'center'}>
                                        {selectedWorkspaceId === item.key && FEATURE_FLAG_WORKSPACE_ACTIONS ? (
                                            <HasPermission
                                                operations={[OPERATION.WORKSPACE_MANAGEMENT]}
                                                Fallback={
                                                    <CustomTabItem
                                                        name={item.name as string}
                                                        isMoreIconVisible={false}
                                                    />
                                                }
                                            >
                                                <CustomTabItemWithMenu
                                                    name={item.name as string}
                                                    isMoreIconVisible={item.key === selectedWorkspaceId}
                                                    id={item.id as string}
                                                    items={items}
                                                    onAction={handleMenuAction}
                                                />
                                            </HasPermission>
                                        ) : (
                                            <CustomTabItem name={item.name as string} isMoreIconVisible={false} />
                                        )}
                                    </Flex>
                                    {FEATURE_FLAG_WORKSPACE_ACTIONS && (
                                        <HasPermission operations={[OPERATION.WORKSPACE_MANAGEMENT]}>
                                            <DeleteDialog
                                                name={item.name as string}
                                                title={'workspace'}
                                                onAction={handleDeleteWorkspace}
                                                triggerState={deleteDialog.deleteWorkspaceDialogState}
                                            />
                                            <EditNameDialog
                                                isLoading={editDialog.editWorkspaceMutation.isPending}
                                                triggerState={editDialog.editWorkspaceDialogState}
                                                onAction={handleEditDialog}
                                                defaultName={item.name as string}
                                                names={workspacesNames.filter((name) => name !== item.name)}
                                                title={'workspace name'}
                                                nameLimitations={{
                                                    maxLength: MAX_LENGTH_OF_WORKSPACE_NAME,
                                                    minLength: MIN_LENGTH_OF_WORKSPACE_NAME,
                                                }}
                                            />
                                        </HasPermission>
                                    )}
                                </>
                            </Item>
                        )}
                    </TabList>

                    {numberOfWorkspaces > MAX_NUMBER_OF_DISPLAYED_WORKSPACES && (
                        <CollapsedItemsPicker
                            hasSelectedPinnedItem={hasSelectedPinnedItem}
                            numberOfCollapsedItems={collapsedItems.length}
                            onSelectionChange={handleSelectWorkspace}
                            items={collapsedItems}
                            ariaLabel={'Collapsed workspaces'}
                        />
                    )}

                    {FEATURE_FLAG_WORKSPACE_ACTIONS && (
                        <HasPermission operations={[OPERATION.WORKSPACE_MANAGEMENT]}>
                            <TooltipTrigger placement={'bottom'}>
                                <ActionButton
                                    isQuiet
                                    id={'create-new-workspace-id'}
                                    aria-label={'Create new workspace'}
                                    onPress={handleCreateWorkspace}
                                    isDisabled={createWorkspace.isPending}
                                >
                                    {createWorkspace.isPending ? <LoadingIndicator size={'S'} /> : <Add />}
                                </ActionButton>
                                <Tooltip>Create a new workspace</Tooltip>
                            </TooltipTrigger>
                        </HasPermission>
                    )}
                </Flex>
                <TabPanels>{(item: TabItem) => <Item key={item.key}>{item.children}</Item>}</TabPanels>
            </Tabs>
        </Flex>
    );
};
