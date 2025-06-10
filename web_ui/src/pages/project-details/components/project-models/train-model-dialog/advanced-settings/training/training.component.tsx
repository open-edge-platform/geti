// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { View } from '@geti/ui';

import { ConfigurableParametersTaskChain } from '../../../../../../../core/configurable-parameters/services/configurable-parameters.interface';
import { FineTuneParameters } from './fine-tune-parameters.component';
import { LearningParameters } from './learning-parameters.component';

interface TrainingProps {
    trainFromScratch: boolean;
    onTrainFromScratchChange: (trainFromScratch: boolean) => void;
    configParameters: ConfigurableParametersTaskChain;

    isReshufflingSubsetsEnabled: boolean;
    onReshufflingSubsetsEnabledChange: (reshufflingSubsetsEnabled: boolean) => void;
}

export const Training: FC<TrainingProps> = ({
    trainFromScratch,
    onTrainFromScratchChange,
    configParameters,
    onReshufflingSubsetsEnabledChange,
    isReshufflingSubsetsEnabled,
}) => {
    const learningParameters = configParameters.components.find(
        (component) => component.header === 'Learning Parameters'
    );

    return (
        <View>
            <FineTuneParameters
                trainFromScratch={trainFromScratch}
                onTrainFromScratchChange={onTrainFromScratchChange}
                isReshufflingSubsetsEnabled={isReshufflingSubsetsEnabled}
                onReshufflingSubsetsEnabledChange={onReshufflingSubsetsEnabledChange}
            />
            {learningParameters?.parameters !== undefined && (
                <LearningParameters parameters={learningParameters.parameters} />
            )}
        </View>
    );
};
