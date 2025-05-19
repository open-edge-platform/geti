// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Content, ContextualHelp, Flex, Radio, RadioGroup, Text } from '@geti/ui';

import { useReconfigAutoTraining } from '../../../../../core/configurable-parameters/hooks/use-reconfig-auto-training.hook';
import { findDynamicRequiredAnnotationsConfig } from '../../../../../core/configurable-parameters/utils';
import { Task } from '../../../../../core/projects/task.interface';
import {
    BooleanGroupParams,
    ConfigurableParametersTaskChain,
    NumberGroupParams,
} from '../../../configurable-parameters/configurable-parameters.interface';
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
    task: Task;
    requiredImagesAutoTrainingConfig: NumberGroupParams;
    dynamicRequiredAnnotationsConfig: BooleanGroupParams;
    autoTrainingOptimisticUpdates: ReturnType<typeof useReconfigAutoTraining>;
    configParameters: ConfigurableParametersTaskChain[];
}

export const AutoTrainingThreshold: FC<AutoTrainingThresholdProps> = ({
    task,
    requiredImagesAutoTrainingConfig,
    dynamicRequiredAnnotationsConfig,
    autoTrainingOptimisticUpdates,
    configParameters,
}) => {
    const selectedThresholdOption = dynamicRequiredAnnotationsConfig.value
        ? AutoTrainingThresholdOption.ADAPTIVE
        : AutoTrainingThresholdOption.FIXED;
    const isFixedThreshold = selectedThresholdOption === AutoTrainingThresholdOption.FIXED;

    const handleThresholdOptionChange = (value: string): void => {
        const isAdaptiveSelected = value === AutoTrainingThresholdOption.ADAPTIVE;

        autoTrainingOptimisticUpdates.mutate({
            configParameters,
            newConfigParameter: {
                ...dynamicRequiredAnnotationsConfig,
                value: isAdaptiveSelected,
            },
            onOptimisticUpdate: (config) => {
                const dynamicRequiredAnnotationsConfigOptimistic = findDynamicRequiredAnnotationsConfig(
                    task.id,
                    config
                );
                if (dynamicRequiredAnnotationsConfigOptimistic !== undefined) {
                    dynamicRequiredAnnotationsConfigOptimistic.value = isAdaptiveSelected;
                }

                return config;
            },
        });
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
                    task={task}
                    autoTrainingOptimisticUpdates={autoTrainingOptimisticUpdates}
                    configParameters={configParameters}
                    requiredImagesAutoTrainingConfig={requiredImagesAutoTrainingConfig}
                />
            )}
        </>
    );
};
