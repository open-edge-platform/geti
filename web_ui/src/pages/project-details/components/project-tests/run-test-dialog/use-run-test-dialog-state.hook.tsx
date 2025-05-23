// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useEffect, useMemo, useState } from 'react';

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { paths } from '@geti/core/src/services/routes';
import { ActionButton } from '@geti/ui';
import { useQueryClient } from '@tanstack/react-query';
import { isEmpty, noop } from 'lodash-es';
import { useNavigate } from 'react-router-dom';

import { isVisualPromptModel } from '../../../../../core/annotations/services/visual-prompt-service';
import { useModels } from '../../../../../core/models/hooks/use-models.hook';
import { DOMAIN, ProjectIdentifier } from '../../../../../core/projects/core.interface';
import { JobInfoStatus } from '../../../../../core/tests/dtos/tests.interface';
import { useTests } from '../../../../../core/tests/hooks/use-tests.hook';
import { MetricType, Test } from '../../../../../core/tests/tests.interface';
import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';
import { NOTIFICATION_TYPE } from '../../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../notification/notification.component';
import { getUniqueNameFromArray, hasEqualId, isNotCropTask } from '../../../../../shared/utils';
import { SelectableOptimizationType } from '../../../project-details.interface';
import { useProject } from '../../../providers/project-provider/project-provider.component';
import { formatModelName, getModels, getOptimizationTypes, TESTS_OPTIMIZATION_TYPES } from '../../../utils';
import { TestNameErrors } from '../utils';
import { RunTestDialogContentProps } from './run-test-dialog.interface';

const TestButton = ({
    projectIdentifier,
    remove = noop,
}: {
    projectIdentifier: ProjectIdentifier;
    remove?: () => void;
}) => {
    const navigate = useNavigate();

    return (
        <ActionButton
            isQuiet
            onPress={() => {
                navigate(paths.project.tests.index(projectIdentifier));
                remove();
            }}
        >
            See progress
        </ActionButton>
    );
};

export const useRunTestDialogState = ({ handleClose, preselectedModel, modelsGroups }: RunTestDialogContentProps) => {
    const queryClient = useQueryClient();
    const { isTaskChainProject, project } = useProject();
    const { workspaceId, projectId, organizationId } = useProjectIdentifier();

    const { useRunTestMutation, useTestsListQuery } = useTests();
    const { useProjectModelQuery } = useModels();
    const { data: tests } = useTestsListQuery({ workspaceId, projectId, organizationId });
    const runTestMutation = useRunTestMutation();
    const { addNotification } = useNotification();

    const testNames = useMemo(() => tests?.map((test) => test.testName) ?? [], [tests]);

    const [testName, setTestName] = useState<string>(getUniqueNameFromArray(testNames, 'T'));
    const [errorInTestName, setErrorInTestName] = useState<TestNameErrors | null>(null);

    const handleTestNameChange = (newTestName: string) => {
        setTestName(newTestName);

        if (isEmpty(newTestName)) {
            setErrorInTestName(TestNameErrors.EMPTY_NAME);
            return;
        }

        const nameExists = testNames.some((name) => name.toLocaleLowerCase() === newTestName.toLocaleLowerCase());

        if (nameExists) {
            setErrorInTestName(TestNameErrors.EXISTING_NAME);
            return;
        }

        errorInTestName !== null && setErrorInTestName(null);
    };

    const tasks = useMemo(
        () =>
            preselectedModel
                ? project.tasks.filter(hasEqualId(preselectedModel.taskId))
                : project.tasks.filter(isNotCropTask),
        [preselectedModel, project]
    );

    const [selectedTaskId, setSelectedTaskId] = useState(tasks[0].id);

    // models ALWAYS have at least one model: preselected one or the array of the models groups
    const models = useMemo(
        () => getModels(preselectedModel, modelsGroups, selectedTaskId),
        [preselectedModel, modelsGroups, selectedTaskId]
    );

    const [selectedModelsGroupId, setSelectedModelsGroupId] = useState<string | null>(models[0]?.groupId ?? null);

    const selectedModelsGroup = useMemo(
        () => models.find(({ groupId }) => groupId === selectedModelsGroupId),
        [models, selectedModelsGroupId]
    );

    const [selectedModelId, setSelectedModelId] = useState<string | null>(
        selectedModelsGroup?.modelVersions[0]?.id ?? null
    );

    const selectedModel = selectedModelsGroup?.modelVersions.find(
        (modelVersion) => modelVersion.id === selectedModelId
    );

    const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(
        project.datasets.length === 1 ? project.datasets[0].id : null
    );

    const [selectedOptimizationType, setSelectedOptimizationType] = useState<SelectableOptimizationType>({
        ...TESTS_OPTIMIZATION_TYPES['BASE'],
        id: (selectedModelId ?? '') as string,
    });

    const { data: modelDetails, isLoading: isLoadingModel } = useProjectModelQuery(
        selectedModelsGroupId as string,
        selectedModelId as string
    );

    const [selectedMetric, setSelectedMetric] = useState<MetricType | null>(null);

    const shouldShowMetricPicker =
        project.domains.includes(DOMAIN.ANOMALY_DETECTION) || project.domains.includes(DOMAIN.ANOMALY_SEGMENTATION);

    const isRunTestDisabled =
        Boolean(errorInTestName) ||
        !selectedTaskId ||
        !selectedModelsGroupId ||
        !selectedModelId ||
        isLoadingModel ||
        isEmpty(selectedModelsGroup?.modelVersions) ||
        !selectedDatasetId ||
        (shouldShowMetricPicker && !selectedMetric) ||
        runTestMutation.isPending;

    const taskWithNoModels = isTaskChainProject && selectedTaskId && isEmpty(models);

    const defaultDataset = project.datasets.find(({ useForTraining }) => useForTraining);
    const isDefaultDatasetSelected = selectedDatasetId === defaultDataset?.id;

    const isJobRunningOrFinished = (test: Test) =>
        [JobInfoStatus.DONE, JobInfoStatus.EVALUATING, JobInfoStatus.INFERRING].some(
            (jobStatus) => jobStatus === test.jobInfo.status
        );

    const wasTestingSetTestedWithThisConfiguration =
        !isDefaultDatasetSelected &&
        Boolean(
            tests?.some((test) => {
                return (
                    isJobRunningOrFinished(test) &&
                    test.datasetsInfo[0].id === selectedDatasetId &&
                    selectedOptimizationType?.id === test.modelInfo.id && // the test uses the optimized model
                    selectedModel?.version === test.modelInfo.version &&
                    selectedOptimizationType.text === test.modelInfo.optimizationType
                );
            })
        );

    const isTaskSelectionVisible = isTaskChainProject && !preselectedModel;
    const isOptimizationSelectionVisible =
        !preselectedModel?.optimizedModel &&
        selectedModelId &&
        selectedModelsGroupId &&
        selectedModel &&
        selectedModelsGroup &&
        !isVisualPromptModel(selectedModelsGroup);

    const handleChangeModelsGroup = (key: Key | null, modelsInput: ReturnType<typeof getModels>): void => {
        setSelectedModelsGroupId(String(key));

        const newSelectedModel = modelsInput.find(({ groupId }) => groupId === key);
        const newModelId = newSelectedModel?.modelVersions.length === 1 ? newSelectedModel?.modelVersions[0].id : null;

        setSelectedModelId(newModelId);

        setSelectedOptimizationType({ ...TESTS_OPTIMIZATION_TYPES['BASE'], id: newModelId ?? '' });
    };

    const handleChangeModel = (key: Key | null): void => {
        setSelectedModelId(String(key));

        setSelectedOptimizationType({ ...TESTS_OPTIMIZATION_TYPES['BASE'], id: key as string });
    };

    const handleSelectTaskType = (key: Key | null): void => {
        setSelectedTaskId(String(key));

        const defaultModels = getModels(preselectedModel, modelsGroups, key);
        const modelGroupId = preselectedModel || defaultModels.length === 1 ? defaultModels[0].groupId : null;

        handleChangeModelsGroup(modelGroupId, defaultModels);
    };

    const handleSelectMetric = (key: Key): void => {
        setSelectedMetric(key as MetricType);
    };

    const handleRunTest = (): void => {
        if (selectedModelsGroupId && selectedModelId && selectedOptimizationType) {
            const modelId =
                selectedModelId === selectedOptimizationType.id ? selectedModelId : selectedOptimizationType.id;

            const bodyWithoutMetric = {
                modelId,
                name: testName.trim(),
                modelGroupId: selectedModelsGroupId,
                datasetIds: [selectedDatasetId as string],
            };

            const bodyWithMetric = {
                ...bodyWithoutMetric,
                metric: selectedMetric,
            };

            runTestMutation.mutate(
                {
                    projectIdentifier: { workspaceId, projectId, organizationId },
                    body: selectedMetric ? bodyWithMetric : bodyWithoutMetric,
                },
                {
                    onSuccess: async (_, { projectIdentifier }) => {
                        await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.TESTS(projectIdentifier) });

                        addNotification({
                            message: 'Test has started',
                            type: NOTIFICATION_TYPE.INFO,
                            actionButtons: [
                                <TestButton
                                    key='see-progress-button'
                                    projectIdentifier={{ projectId, workspaceId, organizationId }}
                                />,
                            ],
                        });
                        handleClose();
                    },
                }
            );
        }
    };

    const optimizationOptions = useMemo(
        () =>
            getOptimizationTypes(modelDetails)
                .filter((optimizationType) => optimizationType.optimizationType !== 'ONNX')
                .map(({ id, modelName }) => ({
                    id,
                    text: formatModelName(modelName),
                })),
        [modelDetails]
    );

    useEffect(() => {
        // In case of preselected optimized model set selected optimized model by default
        if (preselectedModel?.optimizedModel) {
            setSelectedOptimizationType(preselectedModel.optimizedModel);
        }
    }, [preselectedModel?.optimizedModel]);

    return {
        tasks,
        selectedTaskId,
        handleSelectTaskType,
        isTaskSelectionVisible,

        testName,
        handleTestNameChange,
        errorInTestName,

        models,
        selectedModelId,
        handleChangeModel,
        selectedModelsGroupId,
        selectedModelsGroup,
        handleChangeModelsGroup,
        taskWithNoModels,
        isLoadingModel,

        isOptimizationSelectionVisible,
        optimizationOptions,
        selectedOptimizationType,
        setSelectedOptimizationType,

        shouldShowMetricPicker,
        selectedMetric,
        handleSelectMetric,

        datasets: project.datasets,
        selectedDatasetId,
        setSelectedDatasetId,
        isDefaultDatasetSelected,
        wasTestingSetTestedWithThisConfiguration,

        handleRunTest,
        isRunTestDisabled,
        isRunTestMutationLoading: runTestMutation.isPending,
    };
};
