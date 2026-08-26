// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ActionButton, Flex, Text, View } from '@geti-ui/ui';
import { AddCircle } from '@geti-ui/ui/icons';
import { useNavigate } from 'react-router-dom';

import { paths } from '../../../../constants/paths';
import { useImportDatasetDialog } from '../../providers/import-dataset-dialog-provider.component';
import { ImportDatasetAsNewProject } from '../import-dataset-as-new-project/import-dataset-as-new-project.component';

import classes from './new-project-menu.module.scss';

export const NewProjectCard = () => {
    const navigate = useNavigate();
    const { datasetImportDialogState, setCurrentStep, setCurrentStagedId } = useImportDatasetDialog();

    const handleCreateProject = () => {
        navigate(paths.project.new.pattern, {
            viewTransition: true,
        });
    };

    const handleCreateFromDataset = () => {
        setCurrentStep('uploading');
        setCurrentStagedId(null);
        datasetImportDialogState.open();
    };

    return (
        <Flex gap={'size-300'} height={'100%'}>
            <View UNSAFE_className={classes.card}>
                <ActionButton onPress={handleCreateProject} UNSAFE_className={classes.buttonText}>
                    <AddCircle />
                    <Text>Create new project</Text>
                </ActionButton>
            </View>
            <View UNSAFE_className={classes.card}>
                <ActionButton onPress={handleCreateFromDataset} UNSAFE_className={classes.buttonText}>
                    <AddCircle />
                    <Text>Create project from dataset</Text>
                </ActionButton>
            </View>
            <ImportDatasetAsNewProject dialogState={datasetImportDialogState} />
        </Flex>
    );
};
