// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Flex, Text } from '@adobe/react-spectrum';
import { Switch } from '@geti/ui';

import { useReconfigAutoTraining } from '../../../../../core/configurable-parameters/hooks/use-reconfig-auto-training.hook';
import { findAutoTrainingConfig } from '../../../../../core/configurable-parameters/utils';
import { Task } from '../../../../../core/projects/task.interface';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import {
    BooleanGroupParams,
    ConfigurableParametersTaskChain,
} from '../../../configurable-parameters/configurable-parameters.interface';

interface AutoTrainingConfigSwitchProps {
    task: Task;
    isDisabled: boolean;
    trainingConfig: BooleanGroupParams;
    autoTrainingOptimisticUpdates: ReturnType<typeof useReconfigAutoTraining>;
    configParameters: ConfigurableParametersTaskChain[];
}

export const AutoTrainingConfigSwitch: FC<AutoTrainingConfigSwitchProps> = ({
    task,
    isDisabled,
    autoTrainingOptimisticUpdates,
    configParameters,
    trainingConfig,
}) => {
    const onChange = () => {
        autoTrainingOptimisticUpdates.mutate({
            configParameters,
            newConfigParameter: {
                ...trainingConfig,
                value: !trainingConfig.value,
            },
            onOptimisticUpdate: (config) => {
                const autoTrainingConfig = findAutoTrainingConfig(task.id, config);
                if (autoTrainingConfig !== undefined) {
                    autoTrainingConfig.value = !autoTrainingConfig.value;
                }

                return config;
            },
        });
    };

    return (
        <Flex gap={'size-100'} alignItems={'center'} height='21px'>
            <Switch
                isEmphasized
                justifySelf={'end'}
                aria-label={`Toggle auto training for ${task.title}`}
                isSelected={trainingConfig.value}
                isDisabled={isDisabled}
                onChange={onChange}
                id={`training-switch-${idMatchingFormat(task.title)}`}
                UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-800)' }}
                margin={0}
            />
            <label htmlFor={`training-switch-${idMatchingFormat(task.title)}`}>
                <Text id={`new-annotations-${idMatchingFormat(task.title)}`}>Auto-training</Text>
            </label>
        </Flex>
    );
};
