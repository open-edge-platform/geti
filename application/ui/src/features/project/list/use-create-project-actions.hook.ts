// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useNavigate } from 'react-router';

import { paths } from '../../../constants/paths';
import { useImportDatasetDialog } from '../providers/import-dataset-dialog-provider.component';

export const useCreateProjectActions = () => {
    const navigate = useNavigate();
    const { datasetImportDialogState, setCurrentStep, setCurrentStagedId } = useImportDatasetDialog();

    const createProject = () => {
        navigate(paths.project.new.pattern, { viewTransition: true });
    };

    const createProjectFromDataset = () => {
        setCurrentStep('uploading');
        setCurrentStagedId(null);
        datasetImportDialogState.open();
    };

    return { datasetImportDialogState, createProject, createProjectFromDataset };
};
