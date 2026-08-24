// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button, ButtonGroup } from '@geti-ui/ui';
import { useDeleteStagedDataset } from 'hooks/api/staged-dataset.hook';
import { useImportDatasetToProject } from 'hooks/storage/use-import-dataset-to-project.hook';
import { useTranslation } from 'react-i18next';

import { IMPORT_DATASET_FORM_ID } from './util';

type LabelMappingButtonsProps = {
    stagedDatasetId: string;
    onClose: () => void;
};

export const LabelMappingButtons = ({ stagedDatasetId, onClose }: LabelMappingButtonsProps) => {
    const { t } = useTranslation();
    const { deleteImportEntry } = useImportDatasetToProject();
    const deleteFileMutation = useDeleteStagedDataset({
        stagedDatasetId,
        onSuccess: onClose,
        deleteEntry: () => deleteImportEntry(stagedDatasetId),
    });

    const handleDelete = () => {
        deleteFileMutation.mutate();
    };

    return (
        <ButtonGroup>
            <Button
                onPress={handleDelete}
                variant='negative'
                isPending={deleteFileMutation.isPending}
                isDisabled={deleteFileMutation.isPending}
            >
                {t('common.delete')}
            </Button>

            <Button onPress={onClose} variant='secondary'>
                {t('dataset.hideButton')}
            </Button>

            <Button type='submit' form={IMPORT_DATASET_FORM_ID} variant='accent'>
                {t('common.submitButton')}
            </Button>
        </ButtonGroup>
    );
};
