// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { Button, Flex, Text } from '@geti-ui/ui';
import { Add } from '@geti-ui/ui/icons';
import { useNavigate } from 'react-router';

import { paths } from '../../../../constants/paths';
import { useImportDatasetDialog } from '../../providers/import-dataset-dialog-provider.component';
import { ImportDatasetAsNewProject } from '../import-dataset-as-new-project/import-dataset-as-new-project.component';

export const NewProjectCard = () => {
    const { t } = useTranslation();
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
        <Flex direction={'column'} alignItems={'start'} gap={'size-150'}>
            <Button variant={'accent'} onPress={handleCreateProject}>
                <Add />
                <Text>{t('project.list.createNewProject')}</Text>
            </Button>
            <Button variant={'primary'} onPress={handleCreateFromDataset}>
                <Add />
                <Text>{t('project.list.createProjectFromDataset')}</Text>
            </Button>
            <ImportDatasetAsNewProject dialogState={datasetImportDialogState} />
        </Flex>
    );
};
