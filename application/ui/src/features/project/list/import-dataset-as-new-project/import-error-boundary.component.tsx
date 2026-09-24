// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactNode } from 'react';

import { ErrorBoundary } from 'react-error-boundary';

import { useImportDatasetDialog } from '../../providers/import-dataset-dialog-provider.component';

export const ImportErrorBoundary = ({ children }: { children: ReactNode }) => {
    const { datasetImportDialogState } = useImportDatasetDialog();

    return (
        <ErrorBoundary fallback={null} onError={datasetImportDialogState.close}>
            {children}
        </ErrorBoundary>
    );
};
