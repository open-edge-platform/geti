// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Radio, RadioGroup } from '@geti/ui';

import { Accordion } from '../ui/accordion/accordion.component';

interface FineTuneParametersProps {
    trainFromScratch: boolean;
    onTrainFromScratchChange: (trainFromScratch: boolean) => void;
}

enum TRAINING_WEIGHTS {
    PRE_TRAINED_WEIGHTS = 'Pre-trained weights',
    PREVIOUS_TRAINING_WEIGHTS = 'Previous training weights',
}

export const FineTuneParameters: FC<FineTuneParametersProps> = ({ trainFromScratch, onTrainFromScratchChange }) => {
    const trainingWeight = trainFromScratch
        ? TRAINING_WEIGHTS.PRE_TRAINED_WEIGHTS
        : TRAINING_WEIGHTS.PREVIOUS_TRAINING_WEIGHTS;

    const handleTrainingWeightsChange = (value: string): void => {
        if (value === TRAINING_WEIGHTS.PRE_TRAINED_WEIGHTS) {
            onTrainFromScratchChange(true);
        } else {
            onTrainFromScratchChange(false);
        }
    };

    return (
        <Accordion>
            <Accordion.Title>
                Fine-tune parameters <Accordion.Tag>{trainingWeight}</Accordion.Tag>
            </Accordion.Title>
            <Accordion.Content>
                <Accordion.Description>
                    Fine-tuning is the process of adapting a pre-trained model as the starting point for learning new
                    tasks.
                </Accordion.Description>
                <Accordion.Divider marginY={'size-250'} />
                <RadioGroup label={'Training weights'} value={trainingWeight} onChange={handleTrainingWeightsChange}>
                    <Radio value={TRAINING_WEIGHTS.PREVIOUS_TRAINING_WEIGHTS}>
                        Previous training weights - fine-tune the previous version of your model
                    </Radio>
                    <Radio value={TRAINING_WEIGHTS.PRE_TRAINED_WEIGHTS}>
                        Pre-trained weights - fine-tune the original model
                    </Radio>
                </RadioGroup>
            </Accordion.Content>
        </Accordion>
    );
};
