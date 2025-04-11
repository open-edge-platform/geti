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

import { Key } from 'react';

import { useOverlayTriggerState } from '@react-stately/overlays';

import { useWorkspacesApi } from '../../../core/workspaces/hooks/use-workspaces.hook';
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
