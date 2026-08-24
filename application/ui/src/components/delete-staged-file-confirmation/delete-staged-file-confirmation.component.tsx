// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { AlertDialog, Button, DialogTrigger } from '@geti-ui/ui';
import { useDeleteStagedDataset } from 'hooks/api/staged-dataset.hook';
import { useTranslation } from 'react-i18next';

type DeleteStagedFileConfirmationProps = {
    stagedDatasetId: string;
    deleteEntry: () => void;
};

export const DeleteStagedFileConfirmation = ({ stagedDatasetId, deleteEntry }: DeleteStagedFileConfirmationProps) => {
    const { t } = useTranslation();

    const deleteFileMutation = useDeleteStagedDataset({ stagedDatasetId, deleteEntry });

    const handleCancel = () => {
        deleteFileMutation.mutate();
    };

    return (
        <DialogTrigger>
            <Button variant='secondary' style='fill' aria-label={t('dataset.deleteImportStatusAriaLabel')}>
                Delete
            </Button>
            <AlertDialog
                title={t('dataset.deleteStagedFileTitle')}
                variant='destructive'
                cancelLabel='Cancel'
                autoFocusButton='primary'
                primaryActionLabel='Delete'
                onPrimaryAction={handleCancel}
                isPrimaryActionDisabled={deleteFileMutation.isPending}
            >
                {`Are you sure you want to delete the dataset file "${stagedDatasetId}"?`}
            </AlertDialog>
        </DialogTrigger>
    );
};
