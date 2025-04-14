// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { Divider } from '@adobe/react-spectrum';
import { View } from '@react-spectrum/view';
import { clsx } from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import isEmpty from 'lodash/isEmpty';

import { ANIMATION_PARAMETERS } from '../../../../../shared/animation-parameters/animation-parameters';
import { useTasksWithSupportedAlgorithms } from '../../../hooks/use-tasks-with-supported-algorithms';
import { isDeprecatedAlgorithm, isObsoleteAlgorithm } from '../train-model-dialog/model-templates-selection/utils';
import { ModelCard } from './model-card/model-card.component';
import { ModelVersion } from './model-card/model-card.interface';
import { ModelsContainerHeader } from './models-container-header.component';
import { ModelContainerProps } from './models-container.interface';

import classes from './models-container.module.scss';

export const ModelsContainer = ({
    taskId,
    groupId,
    groupName,
    modelSummary,
    modelVersions,
    modelTemplateId,
    lifecycleStage,
    performanceCategory,
}: ModelContainerProps): JSX.Element => {
    const [areModelsExpanded, setAreModelsExpanded] = useState<boolean>(false);

    const handleShowingModels = () => {
        setAreModelsExpanded((prev) => !prev);
    };

    const hasManyModels = modelVersions.length > 1;
    const modelVersion = isEmpty(modelVersions) ? [] : [{ ...modelVersions[0] }];
    const renderModelVersions: ModelVersion[] = areModelsExpanded ? modelVersions : modelVersion;

    const isObsolete = isObsoleteAlgorithm(lifecycleStage);
    const isDeprecated = isDeprecatedAlgorithm(lifecycleStage);
    const { tasksWithSupportedAlgorithms } = useTasksWithSupportedAlgorithms();
    const algorithm = tasksWithSupportedAlgorithms[taskId].find((algorithms) => algorithms.name === groupName);
    const complexity = algorithm?.gigaflops;

    return (
        <View backgroundColor='gray-75'>
            <ModelsContainerHeader
                onClick={handleShowingModels}
                isObsolete={isObsolete}
                hasManyModels={hasManyModels}
                groupId={groupId}
                groupName={groupName}
                performanceCategory={performanceCategory}
                areModelsExpanded={areModelsExpanded}
                modelSummary={modelSummary}
                isDeprecated={isDeprecated}
            />
            <Divider size='S' />
            <View UNSAFE_className={clsx({ isObsolete: classes.obsolete })}>
                <AnimatePresence mode={'popLayout'}>
                    {renderModelVersions.map((model, index) => {
                        return (
                            <motion.div
                                variants={ANIMATION_PARAMETERS.ANIMATE_LIST}
                                initial={'hidden'}
                                animate={'visible'}
                                exit={'hidden'}
                                custom={index}
                                key={model.id}
                            >
                                <ModelCard
                                    model={model}
                                    taskId={taskId}
                                    isLatestModel={index === 0}
                                    modelTemplateId={modelTemplateId}
                                    isMenuOptionsDisabled={isObsolete || isDeprecated}
                                    complexity={complexity}
                                />
                                {index !== renderModelVersions.length - 1 && <Divider size='S' />}
                            </motion.div>
                        );
                    })}
                </AnimatePresence>
            </View>
        </View>
    );
};
