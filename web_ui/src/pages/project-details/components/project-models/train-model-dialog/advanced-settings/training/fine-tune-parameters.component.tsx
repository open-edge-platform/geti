// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Checkbox, Flex, Radio, RadioGroup } from '@geti/ui';

import { InfoTooltip } from '../../../../../../../shared/components/info-tooltip/info-tooltip.component';
import { Accordion } from '../ui/accordion/accordion.component';

import classes from '../../../legacy-train-model-dialog/train-model-settings-item/train-model-settings-item.module.scss';

interface FineTuneParametersProps {
    trainFromScratch: boolean;
    onTrainFromScratchChange: (trainFromScratch: boolean) => void;

    onReshufflingSubsetsEnabledChange: (isChecked: boolean) => void;
    isReshufflingSubsetsEnabled: boolean;
}

enum TRAINING_WEIGHTS {
    PRE_TRAINED_WEIGHTS = 'Pre-trained weights',
    PREVIOUS_TRAINING_WEIGHTS = 'Previous training weights',
}

export const FineTuneParameters: FC<FineTuneParametersProps> = ({
    trainFromScratch,
    onTrainFromScratchChange,
    isReshufflingSubsetsEnabled,
    onReshufflingSubsetsEnabledChange,
}) => {
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

                <Flex gap={'size-100'} alignItems={'center'} marginTop={'size-100'}>
                    <Checkbox
                        isEmphasized
                        isSelected={isReshufflingSubsetsEnabled}
                        onChange={onReshufflingSubsetsEnabledChange}
                        UNSAFE_className={classes.trainModelCheckbox}
                        isDisabled={trainingWeight === TRAINING_WEIGHTS.PREVIOUS_TRAINING_WEIGHTS}
                    >
                        Reshuffle subsets
                    </Checkbox>
                    <InfoTooltip
                        tooltipText={
                            // eslint-disable-next-line max-len
                            'Reassign all dataset items to train, validation, and test subsets from scratch. Previous splits will not be retained. This option is accessible for Pre-trained weights.'
                        }
                    />
                </Flex>
            </Accordion.Content>
        </Accordion>
    );
};
