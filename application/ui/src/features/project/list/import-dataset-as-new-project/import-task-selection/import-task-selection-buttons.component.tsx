// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button, ButtonGroup } from '@geti-ui/ui';
import { useDeleteStagedDataset, useStagedDataset } from 'hooks/api/staged-dataset.hook';
import { useTranslation } from 'react-i18next';

import { TASK_SELECTION_FORM_ID } from './util';

type ImportTaskSelectionButtonsProps = {
    stagedDatasetId: string;
    onClose: () => void;
    deleteEntry: () => void;
};

export const ImportTaskSelectionButtons = ({
    stagedDatasetId,
    onClose,
    deleteEntry,
}: ImportTaskSelectionButtonsProps) => {
    const { t } = useTranslation();
    const stagedDatasetQuery = useStagedDataset(stagedDatasetId);
    const deleteFileMutation = useDeleteStagedDataset({ stagedDatasetId, onSuccess: onClose, deleteEntry });

    const isPending = deleteFileMutation.isPending;
    const isDisabled = isPending || stagedDatasetQuery.isFetching;

    const handleDeleteJob = () => {
        deleteFileMutation.mutate();
    };

    return (
        <ButtonGroup>
            <Button variant='negative' isPending={isPending} isDisabled={isDisabled} onPress={handleDeleteJob}>
                {t('common.delete')}
            </Button>

            <Button onPress={onClose} isPending={isPending} isDisabled={isDisabled} variant='secondary'>
                {t('dataset.hideButton')}
            </Button>

            <Button type='submit' form={TASK_SELECTION_FORM_ID} variant='primary' isDisabled={isDisabled}>
                {t('project.list.nextButton')}
            </Button>
        </ButtonGroup>
    );
};
