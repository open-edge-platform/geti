// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Outlet } from 'react-router-dom';

import { ExportImportDatasetDialogProvider } from '../../features/dataset-export/components/export-import-dataset-dialog-provider.component';
import { DatasetImportToExistingProjectProvider } from '../../features/dataset-import/providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component';
import { MediaProvider } from '../../pages/media/providers/media-provider.component';
import { DatasetProvider } from '../../providers/dataset-provider/dataset-provider.component';

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
