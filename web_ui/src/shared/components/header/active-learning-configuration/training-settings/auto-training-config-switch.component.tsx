// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FC } from 'react';

import { Flex, Text } from '@adobe/react-spectrum';

import { useReconfigAutoTraining } from '../../../../../core/configurable-parameters/hooks/use-reconfig-auto-training.hook';
import { findAutoTrainingConfig } from '../../../../../core/configurable-parameters/utils';
import { Task } from '../../../../../core/projects/task.interface';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import {
    BooleanGroupParams,
    ConfigurableParametersTaskChain,
} from '../../../configurable-parameters/configurable-parameters.interface';
import { Switch } from '../../../switch/switch.component';

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
