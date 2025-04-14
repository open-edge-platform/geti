// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Outlet } from 'react-router-dom';

import { MediaProvider } from '../../pages/media/providers/media-provider.component';
import { DatasetImportToExistingProjectProvider } from '../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component';
import { DatasetProvider } from '../../providers/dataset-provider/dataset-provider.component';
import { ExportImportDatasetDialogProvider } from './../../pages/project-details/components/project-dataset/export-dataset/export-import-dataset-dialog-provider.component';

export const DatasetRoute = () => {
    return (
        <DatasetProvider>
            <MediaProvider>
                <DatasetImportToExistingProjectProvider>
                    <ExportImportDatasetDialogProvider>
                        <Outlet />
                    </ExportImportDatasetDialogProvider>
                </DatasetImportToExistingProjectProvider>
            </MediaProvider>
        </DatasetProvider>
    );
};
