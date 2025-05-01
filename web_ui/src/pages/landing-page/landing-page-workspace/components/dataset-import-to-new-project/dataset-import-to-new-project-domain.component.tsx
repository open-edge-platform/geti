// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useEffect, useMemo, useState } from 'react';

import { ComboBox, Flex, Item } from '@adobe/react-spectrum';
import { LimitedTextField } from '@shared/components/limited-text-field/limited-text-field.component';
import { ValidationErrorMsg } from '@shared/components/validation-error-msg/validation-error-msg.component';
import isEmpty from 'lodash/isEmpty';
import { ValidationError } from 'yup';

import { DATASET_IMPORT_DOMAIN, DATASET_IMPORT_TASK_TYPE } from '../../../../../core/datasets/dataset.enum';
import {
    DatasetImportLabel,
    DatasetImportSupportedProjectType,
    DatasetImportTask,
    DatasetImportToNewProjectItem,
} from '../../../../../core/datasets/dataset.interface';
import { getRandomDistinctColor } from '../../../../create-project/components/distinct-colors';
import {
    MAX_NUMBER_OF_CHARACTERS_OF_PROJECT_NAME,
    ProjectNameErrorPath,
    projectNameSchema,
} from '../../../../create-project/components/utils';
import { isYupValidationError } from '../../../../user-management/profile-page/utils';
import { getDatasetImportDomain, isTaskChainedProject, sortProjectTypes } from './utils';

interface DatasetImportToNewProjectDomainProps {
    datasetImportItem: DatasetImportToNewProjectItem;
    patchDatasetImport: (item: Partial<DatasetImportToNewProjectItem>) => void;
    anomalyRevamp: boolean;
}

const DEFAULT_PROJECT_NAME = 'Project';

export const DatasetImportToNewProjectDomain = ({
    datasetImportItem,
    patchDatasetImport,
    anomalyRevamp,
}: DatasetImportToNewProjectDomainProps): JSX.Element => {
    const { id, supportedProjectTypes, projectName, taskType } = datasetImportItem;

    const [errorMessage, setErrorMessage] = useState<string | undefined>(undefined);

    const projectTypes: DatasetImportSupportedProjectType[] = useMemo((): DatasetImportSupportedProjectType[] => {
        const filteredProjectTypes: DatasetImportSupportedProjectType[] = supportedProjectTypes.filter(
            (supportedProjectType: DatasetImportSupportedProjectType): boolean => {
                return !isEmpty(
                    supportedProjectType.pipeline.tasks.filter(
                        (task: DatasetImportTask): boolean => !isEmpty(task.labels)
                    )
                );
            }
        );

        return !isEmpty(filteredProjectTypes) ? filteredProjectTypes : supportedProjectTypes;
    }, [supportedProjectTypes]);

    const validateProjectName = (name: string): void => {
        try {
            projectNameSchema().validateSync({ name }, { abortEarly: false });
            setErrorMessage(undefined);
        } catch (error: unknown) {
            if (isYupValidationError(error)) {
                error.inner.forEach(({ path, message }: ValidationError) => {
                    if (path === ProjectNameErrorPath.NAME) {
                        setErrorMessage(message);
                    }
                });
            }
        }
    };

    const handleProjectName = (value: string): void => {
        validateProjectName(value);
        patchDatasetImport({ id, projectName: value });
    };

    const handleTaskTypeChange = (selectedType: Key | null) => {
        if (selectedType === null) return;

        const selectedTaskType = selectedType as DATASET_IMPORT_TASK_TYPE;

        const selectedTask: DatasetImportSupportedProjectType = projectTypes.find(
            ({ projectType }): boolean => projectType === selectedTaskType
        ) as DatasetImportSupportedProjectType;

        let firstChainTaskType: DATASET_IMPORT_TASK_TYPE | null = null;

        const firstChainLabels: DatasetImportLabel[] = [];
        const labelsToSelect: DatasetImportLabel[] = [];

        if (isTaskChainedProject(selectedTaskType)) {
            const [firstTaskType, secondTaskType] = selectedTaskType.toString().split('_');

            const tasks = projectTypes.filter(({ projectType }) => projectType === selectedTaskType).at(0);

            const firstChainTasks = tasks?.pipeline.tasks.filter((task) => task.taskType === firstTaskType).at(0);

            const secondChainTask = tasks?.pipeline.tasks.filter((task) => task.taskType === secondTaskType).at(0);

            if (firstChainTasks !== undefined && secondChainTask !== undefined) {
                firstChainTaskType = firstChainTasks?.taskType as DATASET_IMPORT_TASK_TYPE;

                firstChainLabels.push(...firstChainTasks.labels);

                labelsToSelect.push(...secondChainTask.labels);
            }
        } else {
            labelsToSelect.push(
                ...selectedTask.pipeline.tasks.flatMap(
                    (datasetImportTask: DatasetImportTask) => datasetImportTask.labels
                )
            );
        }

        patchDatasetImport({
            id,
            firstChainTaskType,
            firstChainLabels,
            labelsToSelect,
            taskType: selectedTaskType,
            labels: [...firstChainLabels, ...labelsToSelect],
            labelColorMap: Object.fromEntries(
                [...firstChainLabels, ...labelsToSelect].map((label: DatasetImportLabel) => [
                    label.name,
                    getRandomDistinctColor(),
                ])
            ),
        });
    };

    useEffect(() => {
        if (!projectName) handleProjectName(DEFAULT_PROJECT_NAME);
        if (taskType !== null) return;

        const selectedTask = projectTypes.length === 1 ? projectTypes[0].projectType : null;

        handleTaskTypeChange(selectedTask);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <div aria-label='dataset-import-to-new-project-domain'>
            <Flex direction='column'>
                <LimitedTextField
                    width='100%'
                    value={projectName}
                    marginBottom={'size-50'}
                    aria-label='Project name'
                    label='Project name'
                    onFocus={(event) => (event.target as HTMLInputElement).select()}
                    maxLength={MAX_NUMBER_OF_CHARACTERS_OF_PROJECT_NAME}
                    onChange={handleProjectName}
                />
                {errorMessage && <ValidationErrorMsg errorMsg={errorMessage} />}
                <ComboBox
                    width='100%'
                    label='Task type'
                    menuTrigger='focus'
                    items={sortProjectTypes(projectTypes)}
                    marginTop='size-225'
                    allowsCustomValue={false}
                    inputValue={getDatasetImportDomain(taskType as DATASET_IMPORT_TASK_TYPE, anomalyRevamp)}
                    onSelectionChange={handleTaskTypeChange}
                    aria-label={'Project type'}
                >
                    {(option: DatasetImportSupportedProjectType) => {
                        const taskDomain: DATASET_IMPORT_DOMAIN | undefined = getDatasetImportDomain(
                            option.projectType as DATASET_IMPORT_TASK_TYPE,
                            anomalyRevamp
                        );

                        return (
                            <Item textValue={taskDomain} key={option.projectType}>
                                {taskDomain}
                            </Item>
                        );
                    }}
                </ComboBox>
            </Flex>
        </div>
    );
};
