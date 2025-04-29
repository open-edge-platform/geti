// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, Key, useState } from 'react';

import { Flex, Heading } from '@adobe/react-spectrum';

import { ModelGroupsAlgorithmDetails } from '../../../../core/models/models.interface';
import { useIsTraining } from './hooks/use-is-training.hook';
import { ModelsContainer } from './models-container/models-container.component';
import { MODEL_SORTING_FUNCTIONS, ModelsSorting, ModelsSortingOptions } from './models-sorting.component';
import { TrainingProgress } from './training-progress/training-progress.component';

interface ModelsGroupsSingleTaskProps {
    modelsGroups: ModelGroupsAlgorithmDetails[];
    taskName?: string;
}

const ModelsHeader: FC<{
    taskName?: string;
    selectedSortingOption: ModelsSortingOptions;
    onSort: (key: Key) => void;
}> = ({ taskName, selectedSortingOption, onSort }) => {
    if (taskName === undefined) {
        return (
            <Flex alignItems={'center'} justifyContent={'end'}>
                <ModelsSorting onSort={onSort} selectedSortingOption={selectedSortingOption} />
            </Flex>
        );
    }

    return (
        <Flex alignItems={'center'} justifyContent={'space-between'}>
            <Heading level={2} margin={0}>
                {taskName}
            </Heading>
            <ModelsSorting onSort={onSort} selectedSortingOption={selectedSortingOption} />
        </Flex>
    );
};

export const ModelsGroupsSingleTask = ({ modelsGroups, taskName }: ModelsGroupsSingleTaskProps): JSX.Element => {
    const isTraining = useIsTraining();

    const [selectedSortingOption, setSelectedSortingOption] = useState<ModelsSortingOptions>(
        ModelsSortingOptions.ACTIVE_MODEL_ASC
    );

    const sortedModelsGroups = MODEL_SORTING_FUNCTIONS[selectedSortingOption](modelsGroups);

    const handleModelsSort = (key: Key): void => {
        setSelectedSortingOption(key as ModelsSortingOptions);
    };

    return (
        <Flex height={'100%'} direction={'column'} gap={'size-200'}>
            {isTraining && <TrainingProgress taskId={modelsGroups[0].taskId} />}

            <ModelsHeader selectedSortingOption={selectedSortingOption} onSort={handleModelsSort} taskName={taskName} />

            <Flex flex={1} direction={'column'} gap={'size-200'}>
                {sortedModelsGroups.map(
                    ({
                        groupId,
                        groupName,
                        taskId,
                        modelTemplateId,
                        modelVersions,
                        modelSummary,
                        lifecycleStage,
                        isDefaultAlgorithm,
                        performanceCategory,
                        complexity,
                    }) => (
                        <ModelsContainer
                            key={groupId}
                            groupId={groupId}
                            taskId={taskId}
                            groupName={groupName}
                            modelSummary={modelSummary}
                            modelVersions={modelVersions}
                            lifecycleStage={lifecycleStage}
                            modelTemplateId={modelTemplateId}
                            isDefaultAlgorithm={isDefaultAlgorithm}
                            performanceCategory={performanceCategory}
                            complexity={complexity}
                        />
                    )
                )}
            </Flex>
        </Flex>
    );
};
