// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createContext, Dispatch, ReactNode, useContext, useMemo, useState } from 'react';

import { OverlayTriggerState, useOverlayTriggerState } from 'react-stately';

import { ImportDatasetToProjectState } from '../../../shared/import-dataset-state';

type ImportDatasetDialogStateContextProps = {
    datasetImportDialogState: OverlayTriggerState;
    currentStagedId: string | null;
    setCurrentStagedId: Dispatch<React.SetStateAction<string | null>>;
    currentStep: ImportDatasetToProjectState;
    setCurrentStep: Dispatch<React.SetStateAction<ImportDatasetToProjectState>>;
};

const ImportDatasetDialogStateContext = createContext<ImportDatasetDialogStateContextProps | undefined>(undefined);

export const ImportDatasetDialogStateProvider = ({ children }: { children: ReactNode }) => {
    const datasetImportDialogState = useOverlayTriggerState({});
    const [currentStep, setCurrentStep] = useState<ImportDatasetToProjectState>('uploading');
    const [currentStagedId, setCurrentStagedId] = useState<string | null>(null);

    const value = useMemo(
        () => ({ datasetImportDialogState, currentStagedId, setCurrentStagedId, currentStep, setCurrentStep }),
        [datasetImportDialogState, currentStagedId, currentStep]
    );

    return <ImportDatasetDialogStateContext value={value}>{children}</ImportDatasetDialogStateContext>;
};

export const useImportDatasetDialogState = () => {
    const context = useContext(ImportDatasetDialogStateContext);

    if (context === undefined) {
        throw new Error('useImportDatasetDialogState was used outside of ImportDatasetDialogStateProvider');
    }

    return context;
};
