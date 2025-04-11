// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { createContext, ReactNode, useContext } from 'react';

import { useOverlayTriggerState } from '@react-stately/overlays';
import { OverlayTriggerState } from 'react-stately';

import { MissingProviderError } from '../../../../../shared/missing-provider-error';

interface ExportImportDatasetDialogContextProps {
    exportDialogState: OverlayTriggerState;
    datasetImportDialogState: OverlayTriggerState;
}

const ExportImportDatasetDialogContext = createContext<ExportImportDatasetDialogContextProps | undefined>(undefined);

interface ExportImportDatasetDialogContextState {
    children: ReactNode;
}

export const ExportImportDatasetDialogProvider = ({ children }: ExportImportDatasetDialogContextState) => {
    const exportDialogState = useOverlayTriggerState({});
    const datasetImportDialogState = useOverlayTriggerState({});

    return (
        <ExportImportDatasetDialogContext.Provider
            value={{
                exportDialogState,
                datasetImportDialogState,
            }}
        >
            {children}
        </ExportImportDatasetDialogContext.Provider>
    );
};

export const useExportImportDatasetDialogStates = () => {
    const context = useContext(ExportImportDatasetDialogContext);

    if (context === undefined) {
        throw new MissingProviderError('useExportImportDatasetDialogStates', 'ExportImportDatasetDialogProvider');
    }

    return context;
};
