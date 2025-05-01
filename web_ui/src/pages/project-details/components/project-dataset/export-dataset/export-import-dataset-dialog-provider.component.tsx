// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useContext } from 'react';

import { useOverlayTriggerState } from '@react-stately/overlays';
import { MissingProviderError } from '@shared/missing-provider-error';
import { OverlayTriggerState } from 'react-stately';

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
