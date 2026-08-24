// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { AlertDialog, Content, Text } from '@geti-ui/ui';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { useDeleteDatasetViewMutation } from './api/use-delete-dataset-view';
import { DatasetView } from './type';

type DeleteDatasetViewDialogProps = {
    datasetView: DatasetView;
    onClose: () => void;
};

export const DeleteDatasetViewDialog = ({ datasetView, onClose }: DeleteDatasetViewDialogProps) => {
    const projectId = useProjectIdentifier();
    const deleteDatasetViewMutation = useDeleteDatasetViewMutation();

    const deleteDatasetView = () => {
        deleteDatasetViewMutation.mutate(
            {
                params: {
                    path: {
                        project_id: projectId,
                        dataset_view_id: datasetView.id,
                    },
                },
            },
            {
                onSuccess: onClose,
            }
        );
    };

    return (
        <AlertDialog
            title={`Delete confirmation`}
            primaryActionLabel={'Delete'}
            onPrimaryAction={deleteDatasetView}
            onCancel={onClose}
            secondaryActionLabel={'Close'}
            isPrimaryActionDisabled={deleteDatasetViewMutation.isPending}
        >
            <Content>
                <Text>Are you sure you want to delete the {`"${datasetView.name}"`} dataset view?</Text>
            </Content>
        </AlertDialog>
    );
};
