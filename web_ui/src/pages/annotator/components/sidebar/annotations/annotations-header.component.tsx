// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Heading } from '@adobe/react-spectrum';
import { isEmpty, isNil } from 'lodash-es';

import { DOMAIN } from '../../../../../core/projects/core.interface';
import { FEATURES_KEYS } from '../../../../../core/user-settings/dtos/user-settings.interface';
import { getSettingsOfType } from '../../../../../core/user-settings/utils';
import { useAnnotatorMode } from '../../../hooks/use-annotator-mode';
import { useIsSceneBusy } from '../../../hooks/use-annotator-scene-interaction-state.hook';
import { useAnnotator } from '../../../providers/annotator-provider/annotator-provider.component';
import { usePrediction } from '../../../providers/prediction-provider/prediction-provider.component';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { PredictionScoreThreshold } from './prediction-score-threshold.component';

export const AnnotationsHeader = (): JSX.Element => {
    const isSceneBusy = useIsSceneBusy();

    const { userProjectSettings } = useAnnotator();
    const { predictionAnnotations } = usePrediction();
    const { isActiveLearningMode } = useAnnotatorMode();
    const { isTaskChainDomainSelected, selectedTask } = useTask();

    const isAlltask = isNil(selectedTask);
    const featuresConfig = getSettingsOfType(userProjectSettings.config, FEATURES_KEYS);
    const isPredictionAsInitialAnnotations = Boolean(featuresConfig[FEATURES_KEYS.INITIAL_PREDICTION].isEnabled);
    const isTaskChainSelectedClassification = isTaskChainDomainSelected(DOMAIN.CLASSIFICATION);

    const isLearningModeWithThreshold = isActiveLearningMode && isPredictionAsInitialAnnotations;

    // Disable the threshold if we're on 'All tasks' mode or on a task-chain classification task
    const isPredictionScoreThresholdDisabled = isTaskChainSelectedClassification || !selectedTask;
    const hasScoreThreshold = !isActiveLearningMode || isLearningModeWithThreshold;

    const scoreThresholdTooltipDescription = isTaskChainSelectedClassification
        ? 'Filter by score is not applicable in a task-chain project while on a classification task'
        : 'Filter by score is not applicable in "All tasks" mode, you can filter per score only in single task mode';

    const scoreThresholdTooltip = {
        enabled: isPredictionScoreThresholdDisabled,
        description: scoreThresholdTooltipDescription,
    };

    return (
        <Flex justifyContent='space-between' alignItems='center' width={'100%'}>
            <Heading level={4} UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-900)' }}>
                {isActiveLearningMode ? 'Annotations' : 'Predictions'}
            </Heading>
            {!isAlltask && hasScoreThreshold && (
                <PredictionScoreThreshold
                    tooltip={scoreThresholdTooltip}
                    isDisabled={isPredictionScoreThresholdDisabled || isEmpty(predictionAnnotations) || isSceneBusy}
                />
            )}
        </Flex>
    );
};
