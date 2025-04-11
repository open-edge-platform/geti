// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
