// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex } from '@adobe/react-spectrum';
import { Heading } from '@react-spectrum/text';
import isEmpty from 'lodash/isEmpty';
import isNil from 'lodash/isNil';

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
