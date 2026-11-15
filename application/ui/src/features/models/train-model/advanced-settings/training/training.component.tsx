// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Dispatch, SetStateAction } from 'react';

import type { TrainingConfiguration } from '@/api/types';
import { View } from '@geti-ui/ui';

import { findGroupByKey } from '../../../model-listing/model-training-parameters/utils';
import { Accordion } from '../components/accordion/accordion.component';
import { Parameters } from '../components/parameters.component';
import { deepReplaceParameters } from '../utils';
import { LearningParameters } from './learning-parameters/learning-parameters.component';
import { getLearningParameters } from './learning-parameters/utils';

type TrainingProps = {
    trainingConfiguration: TrainingConfiguration;
    defaultTrainingConfiguration: TrainingConfiguration;
    onTrainingConfigurationChange: Dispatch<SetStateAction<TrainingConfiguration | undefined>>;
};

export const Training = ({
    trainingConfiguration,
    defaultTrainingConfiguration,
    onTrainingConfigurationChange,
}: TrainingProps) => {
    const learningParameters = getLearningParameters(trainingConfiguration);
    const defaultLearningParameters = getLearningParameters(defaultTrainingConfiguration);
    const evaluation = findGroupByKey(trainingConfiguration.parameters, 'evaluation');

    return (
        <View>
            {learningParameters !== undefined && (
                <LearningParameters
                    learningParameters={learningParameters}
                    defaultLearningParameters={defaultLearningParameters}
                    onTrainingConfigurationChange={onTrainingConfigurationChange}
                />
            )}
            {evaluation !== undefined && (
                <Accordion>
                    <Accordion.Title>{evaluation.name}</Accordion.Title>
                    <Accordion.Content>
                        <Accordion.Description>{evaluation.description}</Accordion.Description>
                        <Accordion.Divider marginY={'size-250'} />
                        <Parameters
                            parameters={evaluation.parameters}
                            onChange={(parameter, groupKeys = []) =>
                                onTrainingConfigurationChange((config) =>
                                    config === undefined
                                        ? undefined
                                        : {
                                              ...config,
                                              parameters: deepReplaceParameters(
                                                  config.parameters,
                                                  [parameter],
                                                  ['evaluation', ...groupKeys]
                                              ),
                                          }
                                )
                            }
                        />
                    </Accordion.Content>
                </Accordion>
            )}
        </View>
    );
};
