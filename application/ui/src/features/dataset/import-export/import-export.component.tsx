// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ActionButton, Item, Key, Menu, MenuTrigger, Tooltip, TooltipTrigger } from '@geti-ui/ui';
import { DownloadIcon, Share } from '@geti-ui/ui/icons';
import { useOverlayTriggerState } from '@react-stately/overlays';

import { ReactComponent as ImportExportIcon } from '../../../assets/icons/import-export.svg';
import { ExportDatasetConfig } from '../../../components/export-dataset-config-dialog/export-dataset-config.component';
import { useImportDatasetDialogState } from '../providers/export-import-dataset-dialog-provider.component';
import { MainDatasetStatistics } from './export-dataset/dataset-statistics.component';
import { ImportDatasetToProject } from './import-dataset/Import-dataset-to-project.component';

export const ImportExport = () => {
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
            <TooltipTrigger>
                <ActionButton isQuiet aria-label='Import dataset' onPress={datasetImportDialogState.open}>
                    <Share />
                </ActionButton>
                <Tooltip>Import dataset</Tooltip>
            </TooltipTrigger>

            <TooltipTrigger>
                <ActionButton isQuiet aria-label='Export dataset' onPress={exportDialogState.open}>
                    <DownloadIcon />
                </ActionButton>
                <Tooltip>Export dataset</Tooltip>
            </TooltipTrigger>

            <ImportDatasetToProject />

            <ExportDatasetConfig
                datasetId={null}
                dialogState={exportDialogState}
                statistics={<MainDatasetStatistics />}
            />
        </>
    );
};
