// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useActionState, useState } from 'react';

import type { TaskType } from '@/api/types';
import { Flex, Form, Item, Picker, Text, TextField, View } from '@geti-ui/ui';
import { InfoOutline } from '@geti-ui/ui/icons';
import { useProjects } from 'hooks/api/project.hook';
import { useStagedDatasetSuspense } from 'hooks/api/staged-dataset.hook';
import { useImportDatasetAsNewProject } from 'hooks/storage/use-import-dataset-as-new-project.hook';
import { useTranslation } from 'react-i18next';

import { generateUniqueProjectName } from '../../../create/utils';
import { useImportDatasetDialog } from '../../../providers/import-dataset-dialog-provider.component';
import { validateProjectName } from '../../../validator';
import { getAllowedTaskTypes, getRecommendedTaskType, TASK_SELECTION_FORM_ID } from './util';

type ImportTaskSelectionProps = {
    stagedDatasetId: string;
};

const useFormConfig = (
    stagedDatasetId: string,
    defaultTaskType: TaskType | undefined,
    allowedTaskTypes: TaskType[]
) => {
    const { data: projects } = useProjects();
    const { setCurrentStep } = useImportDatasetDialog();
    const { getImportEntry, updateImportEntry } = useImportDatasetAsNewProject();
    const importEntry = getImportEntry(stagedDatasetId);

    const uniqueProjectName = generateUniqueProjectName(projects.map((project) => project.name));

    const taskType = importEntry?.project?.task_type;
    const finalTaskType = taskType && allowedTaskTypes.includes(taskType) ? taskType : defaultTaskType;

    const initialFormState = {
        name: importEntry?.project?.name ?? uniqueProjectName,
        task_type: finalTaskType,
    };

    return useActionState<{ name: string; task_type: TaskType | undefined }, FormData>(async (_prevState, formData) => {
        const project = {
            name: String(formData.get('name')).trim(),
            task_type: formData.get('task_type') as TaskType,
        };

        setCurrentStep('labelMapping');
        updateImportEntry(stagedDatasetId, { project, step: 'labelMapping' });
        return project;
    }, initialFormState);
};

export const ImportTaskSelection = ({ stagedDatasetId }: ImportTaskSelectionProps) => {
    const { t } = useTranslation();
    const { data: projects } = useProjects();
    const { data: stagedDataset } = useStagedDatasetSuspense(stagedDatasetId);

    const annotationType = stagedDataset?.metadata?.annotation_type;
    const isGetiFormat = stagedDataset.format === 'geti';
    const allowedTaskTypes = getAllowedTaskTypes(annotationType);
    const defaultTaskType = isGetiFormat ? getRecommendedTaskType(annotationType) : undefined;

    const [formState, submitAction] = useFormConfig(stagedDatasetId, defaultTaskType, allowedTaskTypes);
    const [name, setName] = useState(formState.name);

    const validationErrorMessage = validateProjectName(
        name.trim(),
        projects.map((project) => project.name)
    );

    const items = allowedTaskTypes.map((taskType) => ({
        key: taskType,
        label:
            defaultTaskType === taskType
                ? t('projectList.importTask.recommended', { task: t(`taskTypes.${taskType}`) })
                : t(`taskTypes.${taskType}`),
    }));

    return (
        <View backgroundColor={'gray-75'} margin={'size-300'} padding={'size-300'}>
            <Form id={TASK_SELECTION_FORM_ID} validationBehavior='native' action={submitAction}>
                <TextField
                    isRequired
                    name={'name'}
                    value={name}
                    onChange={setName}
                    label={t('projectList.importTask.projectName')}
                    aria-label={'Project name'}
                    defaultValue={formState.name}
                    marginBottom={'size-250'}
                    errorMessage={validationErrorMessage}
                    validationState={validationErrorMessage === undefined ? undefined : 'invalid'}
                />

                <Picker
                    isRequired
                    items={items}
                    name={'task_type'}
                    label={t('projectList.importTask.taskType')}
                    aria-label={'Task type'}
                    marginBottom={'size-150'}
                    placeholder={t('projectList.importTask.selectTask')}
                    defaultSelectedKey={formState.task_type}
                >
                    {(item) => <Item>{item.label}</Item>}
                </Picker>

                <View>
                    {defaultTaskType !== undefined && (
                        <Flex gap='size-100' alignItems={'center'}>
                            <View width={16} height={16}>
                                <InfoOutline />
                            </View>

                            <Text>{t('projectList.importTask.recommendedHint')}</Text>
                        </Flex>
                    )}
                </View>
            </Form>
        </View>
    );
};
