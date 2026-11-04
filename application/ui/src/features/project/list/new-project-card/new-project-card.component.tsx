// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { Button, Flex, Text } from '@geti-ui/ui';
import { Add } from '@geti-ui/ui/icons';

import { ImportDatasetAsNewProject } from '../import-dataset-as-new-project/import-dataset-as-new-project.component';
import { useCreateProjectActions } from '../use-create-project-actions.hook';

export const NewProjectCard = () => {
    const { t } = useTranslation();
    const { datasetImportDialogState, createProject, createProjectFromDataset } = useCreateProjectActions();

    return (
        <Flex direction={'column'} alignItems={'start'} gap={'size-150'}>
            <Button variant={'accent'} onPress={createProject}>
                <Add />
                <Text>{t('project.list.createNewProject')}</Text>
            </Button>
            <Button variant={'primary'} onPress={createProjectFromDataset}>
                <Add />
                <Text>{t('project.list.createProjectFromDataset')}</Text>
            </Button>
            <ImportDatasetAsNewProject dialogState={datasetImportDialogState} />
        </Flex>
    );
};
