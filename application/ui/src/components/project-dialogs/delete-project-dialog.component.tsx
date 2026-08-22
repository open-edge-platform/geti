// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { AlertDialog, DialogContainer } from '@geti-ui/ui';
import { useDeleteProject } from 'hooks/api/project.hook';
import { useTranslation } from 'react-i18next';

import { toast } from '../toast/toast.component';

type DeleteProjectDialogProps = {
    isOpen: boolean;
    projectId: string;
    projectName: string;
    onClose: () => void;
    onDeleted?: () => void;
};

export const DeleteProjectDialog = ({
    isOpen,
    projectId,
    projectName,
    onClose,
    onDeleted,
}: DeleteProjectDialogProps) => {
    const deleteMutation = useDeleteProject();
    const { t } = useTranslation();

    const handleDelete = () => {
        deleteMutation.mutate(
            { params: { path: { project_id: projectId } } },
            {
                onSuccess: () => {
                    onDeleted?.();
                    toast({ type: 'success', message: t('projectDialogs.deletedToast') });
                },
            }
        );
    };

    return (
        <DialogContainer onDismiss={onClose}>
            {isOpen && (
                <AlertDialog
                    title={t('projectDialogs.deleteTitle')}
                    variant='destructive'
                    cancelLabel={t('common.cancel')}
                    primaryActionLabel={t('common.delete')}
                    onPrimaryAction={handleDelete}
                    onSecondaryAction={onClose}
                    autoFocusButton='primary'
                    isPrimaryActionDisabled={deleteMutation.isPending}
                >
                    {t('projectDialogs.deleteConfirmationText', { projectName })}
                </AlertDialog>
            )}
        </DialogContainer>
    );
};
