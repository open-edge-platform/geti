// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ExportDatasetConfig } from '@/components/export-dataset-config-dialog/export-dataset-config.component';
import { Button, Item, Key, Menu, MenuTrigger } from '@geti-ui/ui';
import { useOverlayTriggerState } from '@react-stately/overlays';

import { useDatasetViewId } from '../../../hooks/use-dataset-view-id.hook';
import { useDatasetViewsQuery } from '../../dataset/gallery/toolbar/dataset-view-selector/api/use-dataset-views';
import { useImportDatasetDialogState } from '../providers/export-import-dataset-dialog-provider.component';
import { MainDatasetStatistics } from './export-dataset/dataset-statistics.component';
import { ImportDatasetToProject } from './import-dataset/Import-dataset-to-project.component';

export const ImportExport = () => {
    const exportDialogState = useOverlayTriggerState({});
    const { datasetImportDialogState, setCurrentStep } = useImportDatasetDialogState();
    const [datasetViewId] = useDatasetViewId();
    const { data: viewsData } = useDatasetViewsQuery();
    const datasetViewName =
        datasetViewId && datasetViewId !== 'all'
            ? viewsData?.find((v: { id: string; name: string }) => v.id === datasetViewId)?.name
            : undefined;

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
                <Button variant='secondary' aria-label='import export dataset'>
                    Export/Import
                </Button>
                <Menu onAction={handleMenuAction}>
                    <Item key='export'>Export dataset</Item>
                    <Item key='import'>Import dataset</Item>
                </Menu>
            </MenuTrigger>

            <ImportDatasetToProject />

            <ExportDatasetConfig
                datasetId={null}
                datasetViewId={datasetViewId === 'all' || datasetViewId === null ? undefined : datasetViewId}
                datasetViewName={datasetViewName}
                dialogState={exportDialogState}
                statistics={
                    <MainDatasetStatistics
                        datasetViewId={datasetViewId === 'all' || datasetViewId === null ? undefined : datasetViewId}
                    />
                }
            />
        </>
    );
};
