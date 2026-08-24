// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button, Item, Key, Menu, MenuTrigger } from '@geti-ui/ui';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { useTranslation } from 'react-i18next';

import { ExportDatasetConfig } from '../../../components/export-dataset-config-dialog/export-dataset-config.component';
import { useImportDatasetDialogState } from '../providers/export-import-dataset-dialog-provider.component';
import { MainDatasetStatistics } from './export-dataset/dataset-statistics.component';
import { ImportDatasetToProject } from './import-dataset/Import-dataset-to-project.component';

export const ImportExport = () => {
    const { t } = useTranslation();

    const exportDialogState = useOverlayTriggerState({});
    const { datasetImportDialogState, setCurrentStep } = useImportDatasetDialogState();

    const handleMenuAction = (option: Key) => {
        switch (option) {
            case 'export':
                exportDialogState.open();
                break;

            case 'import':
                setCurrentStep('uploading');
                datasetImportDialogState.open();
                break;
        }
    };

    return (
        <>
            <MenuTrigger>
                <Button variant='secondary' aria-label={t('dataset.importExportButtonAriaLabel')}>
                    {t('dataset.exportImportText')}
                </Button>
                <Menu onAction={handleMenuAction}>
                    <Item key='export'>{t('dataset.exportDataset')}</Item>
                    <Item key='import'>{t('dataset.importDataset')}</Item>
                </Menu>
            </MenuTrigger>

            <ImportDatasetToProject />

            <ExportDatasetConfig
                datasetId={null}
                dialogState={exportDialogState}
                statistics={<MainDatasetStatistics />}
            />
        </>
    );
};
