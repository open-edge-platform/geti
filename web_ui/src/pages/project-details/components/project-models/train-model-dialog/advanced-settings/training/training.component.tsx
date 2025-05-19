// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { View } from '@geti/ui';

import { ConfigurableParametersTaskChain } from '../../../../../../../shared/components/configurable-parameters/configurable-parameters.interface';
import { FineTuneParameters } from './fine-tune-parameters.component';
import { LearningParameters } from './learning-parameters.component';

interface TrainingProps {
    trainFromScratch: boolean;
    onTrainFromScratchChange: (trainFromScratch: boolean) => void;
    configParameters: ConfigurableParametersTaskChain;
}

export const Training: FC<TrainingProps> = ({ trainFromScratch, onTrainFromScratchChange, configParameters }) => {
    const learningParameters = configParameters.components.find(
        (component) => component.header === 'Learning Parameters'
    );

    return (
        <View>
            <FineTuneParameters
                trainFromScratch={trainFromScratch}
                onTrainFromScratchChange={onTrainFromScratchChange}
            />
            {learningParameters?.parameters !== undefined && (
                <LearningParameters parameters={learningParameters.parameters} />
            )}
        </View>
    );
};
