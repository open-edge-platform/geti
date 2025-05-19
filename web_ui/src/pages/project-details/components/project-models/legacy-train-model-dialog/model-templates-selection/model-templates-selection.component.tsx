// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, Key, SetStateAction, useEffect, useMemo, useState } from 'react';

import { Flex, Radio, RadioGroup, View } from '@geti/ui';
import { isEmpty } from 'lodash-es';

import { ModelsGroups } from '../../../../../../core/models/models.interface';
import { isActiveModel } from '../../../../../../core/models/utils';
import { Task } from '../../../../../../core/projects/task.interface';
import {
    SupportedAlgorithm,
    TaskWithSupportedAlgorithms,
} from '../../../../../../core/supported-algorithms/supported-algorithms.interface';
import { InfoTooltip } from '../../../../../../shared/components/info-tooltip/info-tooltip.component';
import { isNotCropTask } from '../../../../../../shared/utils';
import { useProject } from '../../../../providers/project-provider/project-provider.component';
import { ModelTemplatesList } from './model-templates-list/model-templates-list.component';
import { TaskSelection } from './task-selection.component';
import {
    CUSTOM_MODEL_CONFIG_TOOLTIP_TEXT,
    isObsoleteAlgorithm,
    LATEST_MODEL_CONFIG_TOOLTIP_TEXT,
    ModelConfigurationOption,
} from './utils';

interface ModelTemplatesSelectionProps {
    selectedTask: Task;
    animationDirection: number;
    models: ModelsGroups[] | undefined;
    setSelectedTask: Dispatch<SetStateAction<Task>>;
    modelConfigurationOption: ModelConfigurationOption;
    setModelConfigurationOption: Dispatch<SetStateAction<ModelConfigurationOption>>;

    tasksWithSupportedAlgorithms: TaskWithSupportedAlgorithms;

    selectedModelTemplateId: string | null;
    handleSelectedTemplateId: (modelTemplateId: string | null) => void;
}

export const ModelTemplatesSelection = ({
    models,
    selectedTask,
    setSelectedTask,
    animationDirection,

    selectedModelTemplateId,
    handleSelectedTemplateId,

    tasksWithSupportedAlgorithms,

    modelConfigurationOption,
    setModelConfigurationOption,
}: ModelTemplatesSelectionProps): JSX.Element => {
    const { project, isTaskChainProject } = useProject();
    const { tasks } = project;

    const taskItems = tasks.filter(isNotCropTask);
    const [selectedDomain, setSelectedDomain] = useState<string>(selectedTask.domain);

    const algorithms = useMemo<SupportedAlgorithm[]>(
        () =>
            (tasksWithSupportedAlgorithms[selectedTask.id] ?? []).filter(
                ({ lifecycleStage }) => !isObsoleteAlgorithm(lifecycleStage)
            ),
        [tasksWithSupportedAlgorithms, selectedTask]
    );

    const getActiveModelTemplateIdPerTask = (inputAlgorithms: SupportedAlgorithm[], inputSelectedTaskId: string) => {
        if (isEmpty(inputAlgorithms) || models === undefined) {
            return undefined;
        }

        const activeModelGroupPerTask = models.filter(
            ({ taskId, modelVersions }) => taskId === inputSelectedTaskId && modelVersions.find(isActiveModel)
        );

        // we don't have any models yet
        if (isEmpty(activeModelGroupPerTask) || isEmpty(activeModelGroupPerTask[0].modelVersions)) {
            return inputAlgorithms.find(({ isDefaultAlgorithm }) => isDefaultAlgorithm)?.modelTemplateId;
        }

        return activeModelGroupPerTask[0].modelTemplateId;
    };

    const activeModelTemplateIdPerTask = useMemo<string | undefined>(
        () => getActiveModelTemplateIdPerTask(algorithms, selectedTask.id),
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [models, selectedTask, algorithms]
    );

    const handleInitialTemplateSelection = (
        templates: SupportedAlgorithm[],
        activeModelTemplateId: string | undefined = activeModelTemplateIdPerTask
    ): void => {
        if (activeModelTemplateId === undefined) {
            return;
        }

        const modelToSelect = templates.find(({ modelTemplateId }) => modelTemplateId === activeModelTemplateId);

        // it means that active model is not from the recommended model templates
        if (modelToSelect === undefined) {
            handleSelectedTemplateId(activeModelTemplateId);

            return;
        }

        handleSelectedTemplateId(modelToSelect.modelTemplateId);
    };

    const handleSelectDomainChange = (domain: Key) => {
        // Update selected task and set selected model template to null (in the task chain project)
        // once user changed the task, it will trigger handleModelTemplateSelectedByDefault method to set
        // proper model template

        if (selectedTask.domain === domain) {
            return;
        }

        const newSelectedTask = tasks.find((task) => task.domain === domain) as Task;
        const newAlgorithms = tasksWithSupportedAlgorithms[newSelectedTask.id];
        const newActiveTemplateId = getActiveModelTemplateIdPerTask(newAlgorithms, newSelectedTask.id);

        setSelectedDomain(String(domain));
        setSelectedTask(newSelectedTask);

        handleInitialTemplateSelection(newAlgorithms, newActiveTemplateId);
    };

    useEffect(() => {
        if (selectedModelTemplateId === null) {
            handleInitialTemplateSelection(algorithms, activeModelTemplateIdPerTask);
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeModelTemplateIdPerTask, algorithms, selectedModelTemplateId]);

    if (selectedModelTemplateId === null) {
        return <></>;
    }

    return (
        <>
            {isTaskChainProject ? (
                <View marginBottom={'size-100'}>
                    <TaskSelection
                        selectedTask={selectedDomain}
                        onTaskChange={handleSelectDomainChange}
                        tasks={taskItems}
                    />
                </View>
            ) : (
                <></>
            )}

            <ModelTemplatesList
                templates={algorithms}
                selectedDomain={selectedDomain.toString()}
                animationDirection={animationDirection}
                selectedModelTemplateId={selectedModelTemplateId}
                handleSelectedTemplateId={handleSelectedTemplateId}
                activeModelTemplateIdPerTask={activeModelTemplateIdPerTask}
            />

            <RadioGroup
                value={modelConfigurationOption}
                onChange={(value) => setModelConfigurationOption(value as ModelConfigurationOption)}
                aria-label={'Training model configuration option'}
            >
                <Flex alignItems={'center'}>
                    <Radio
                        value={ModelConfigurationOption.LATEST_CONFIGURATION}
                        aria-label={ModelConfigurationOption.LATEST_CONFIGURATION}
                        marginEnd={'size-100'}
                    >
                        Use the latest model configuration
                    </Radio>
                    <InfoTooltip id={'latest-model-config-id'} tooltipText={LATEST_MODEL_CONFIG_TOOLTIP_TEXT} />
                </Flex>

                <Flex alignItems={'center'}>
                    <Radio
                        value={ModelConfigurationOption.MANUAL_CONFIGURATION}
                        aria-label={ModelConfigurationOption.MANUAL_CONFIGURATION}
                        marginEnd={'size-100'}
                    >
                        Set configurations manually
                    </Radio>
                    <InfoTooltip id={'custom-model-config-id'} tooltipText={CUSTOM_MODEL_CONFIG_TOOLTIP_TEXT} />
                </Flex>
            </RadioGroup>
        </>
    );
};
