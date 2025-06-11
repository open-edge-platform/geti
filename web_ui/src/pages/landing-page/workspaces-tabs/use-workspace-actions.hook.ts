// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { useWorkspacesApi } from '@geti/core/src/workspaces/hooks/use-workspaces.hook';
import { useOverlayTriggerState } from '@react-stately/overlays';

import { WORKSPACES_SETTINGS_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../core/user-settings/hooks/use-global-settings.hook';
import { useOrganizationIdentifier } from '../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { WorkspaceMenuActions } from './utils';

const MIN_NUMBER_OF_REQUIRED_WORKSPACES = 1;

export const useWorkspaceActions = (numberOfWorkspaces: number) => {
    const editWorkspaceDialogState = useOverlayTriggerState({});
    const deleteWorkspaceDialogState = useOverlayTriggerState({});
    const settings = useUserGlobalSettings();

    const { organizationId } = useOrganizationIdentifier();
    const { useEditWorkspaceMutation, useDeleteWorkspaceMutation } = useWorkspacesApi(organizationId);

    const editWorkspaceMutation = useEditWorkspaceMutation();
    const deleteWorkspaceMutation = useDeleteWorkspaceMutation();

    const getAvailableItems = (isDefaultWorkspace: boolean) => {
        const items: WorkspaceMenuActions[] = [WorkspaceMenuActions.EDIT];

        if (numberOfWorkspaces > MIN_NUMBER_OF_REQUIRED_WORKSPACES) {
            items.push(WorkspaceMenuActions.DELETE);
        }
        if (!isDefaultWorkspace) {
            items.push(WorkspaceMenuActions.SET_AS_DEFAULT);
        }

        return items;
    };

    const selectDefaultWorkspace = (workspaceId: string) => {
        settings.saveConfig({
            ...settings.config,
            [WORKSPACES_SETTINGS_KEYS.DEFAULT_WORKSPACE]: { id: workspaceId },
        });
    };

    const handleMenuAction = (key: Key, workspaceId: string) => {
        switch (key.toString().toLocaleLowerCase()) {
            case WorkspaceMenuActions.EDIT.toLocaleLowerCase(): {
                editWorkspaceDialogState.open();

                break;
            }
            case WorkspaceMenuActions.DELETE.toLocaleLowerCase(): {
                deleteWorkspaceDialogState.open();

                break;
            }
            case WorkspaceMenuActions.SET_AS_DEFAULT.toLocaleLowerCase(): {
                selectDefaultWorkspace(workspaceId);

                break;
            }

            default:
                throw new Error(`Handler for ${key} does not exist`);
        }
    };

    return {
        handleMenuAction,
        getAvailableItems,
        deleteDialog: {
            deleteWorkspaceDialogState,
            deleteWorkspaceMutation,
        },
        editDialog: {
            editWorkspaceDialogState,
            editWorkspaceMutation,
        },
    };
};
