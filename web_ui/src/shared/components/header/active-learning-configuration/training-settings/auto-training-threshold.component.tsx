// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Content, ContextualHelp, Flex, Radio, RadioGroup, Text } from '@geti/ui';

import { NumberGroupParams } from '../../../../../core/configurable-parameters/services/configurable-parameters.interface';
import { NumberParameter } from '../../../../../core/configurable-parameters/services/configuration.interface';
import { RequiredAnnotationsSlider } from './required-annotations-slider.component';

enum AutoTrainingThresholdOption {
    FIXED = 'Fixed',
    ADAPTIVE = 'Adaptive',
}

const AutoTrainingThresholdContextualHelp: FC = () => {
    return (
        <ContextualHelp variant='info'>
            <Content>
                <Text>
                    Select {'"Adaptive"'} to let the system dynamically compute the number of required annotations
                    between training rounds based on model performance and training dataset size.
                </Text>
                <br />
                <Text>
                    Select {'"Fixed"'} if you want auto-training to start each time after a specified number of
                    annotations is submitted.
                </Text>
            </Content>
        </ContextualHelp>
    );
};

interface AutoTrainingThresholdProps {
    requiredImagesAutoTrainingConfig: NumberGroupParams | NumberParameter;
    dynamicRequiredAnnotations: boolean;
    onUpdateDynamicRequiredAnnotations: (value: boolean) => void;
    onUpdateRequiredAnnotations: (newNumberOfRequiredAnnotations: number) => void;
}

export const AutoTrainingThreshold: FC<AutoTrainingThresholdProps> = ({
    requiredImagesAutoTrainingConfig,
    dynamicRequiredAnnotations,
    onUpdateRequiredAnnotations,
    onUpdateDynamicRequiredAnnotations,
}) => {
    const selectedThresholdOption = dynamicRequiredAnnotations
        ? AutoTrainingThresholdOption.ADAPTIVE
        : AutoTrainingThresholdOption.FIXED;
    const isFixedThreshold = selectedThresholdOption === AutoTrainingThresholdOption.FIXED;

    const handleThresholdOptionChange = (value: string): void => {
        const isAdaptiveSelected = value === AutoTrainingThresholdOption.ADAPTIVE;

        onUpdateDynamicRequiredAnnotations(isAdaptiveSelected);
    };

    return (
        <>
            <RadioGroup
                label={'Auto-training threshold'}
                contextualHelp={<AutoTrainingThresholdContextualHelp />}
                value={selectedThresholdOption}
                onChange={handleThresholdOptionChange}
            >
                <Flex alignItems={'center'} gap={'size-100'}>
                    <Radio value={AutoTrainingThresholdOption.ADAPTIVE}>{AutoTrainingThresholdOption.ADAPTIVE}</Radio>
                    <Radio value={AutoTrainingThresholdOption.FIXED}>{AutoTrainingThresholdOption.FIXED}</Radio>
                </Flex>
            </RadioGroup>

            {isFixedThreshold && (
                <RequiredAnnotationsSlider
                    requiredImagesAutoTrainingConfig={requiredImagesAutoTrainingConfig}
                    onUpdateRequiredAnnotations={onUpdateRequiredAnnotations}
                />
            )}
        </>
    );
};
