// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { useWorkspacesApi } from '@geti/core/src/workspaces/hooks/use-workspaces.hook';
import { useOverlayTriggerState } from '@react-stately/overlays';

import { useOrganizationIdentifier } from '../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { WorkspaceMenuActions } from './utils';

const MIN_NUMBER_OF_REQUIRED_WORKSPACES = 1;

export const useWorkspaceActions = (numberOfWorkspaces: number) => {
    const editWorkspaceDialogState = useOverlayTriggerState({});
    const deleteWorkspaceDialogState = useOverlayTriggerState({});

    const { organizationId } = useOrganizationIdentifier();
    const { useEditWorkspaceMutation, useDeleteWorkspaceMutation } = useWorkspacesApi(organizationId);

    const editWorkspaceMutation = useEditWorkspaceMutation();
    const deleteWorkspaceMutation = useDeleteWorkspaceMutation();

    const menuItems = (() => {
        const items: WorkspaceMenuActions[] = [WorkspaceMenuActions.EDIT];

        if (numberOfWorkspaces > MIN_NUMBER_OF_REQUIRED_WORKSPACES) {
            items.push(WorkspaceMenuActions.DELETE);
        }

        return items;
    })();

    const handleMenuAction = (key: Key) => {
        switch (key.toString().toLocaleLowerCase()) {
            case WorkspaceMenuActions.EDIT.toLocaleLowerCase(): {
                editWorkspaceDialogState.open();

                break;
            }
            case WorkspaceMenuActions.DELETE.toLocaleLowerCase(): {
                deleteWorkspaceDialogState.open();

                break;
            }

            default:
                throw new Error(`Handler for ${key} does not exist`);
        }
    };

    return {
        items: menuItems,
        handleMenuAction,
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
