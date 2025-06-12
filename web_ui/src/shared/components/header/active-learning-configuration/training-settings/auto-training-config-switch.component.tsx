// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Flex, Switch, Text } from '@geti/ui';

import { Task } from '../../../../../core/projects/task.interface';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';

interface AutoTrainingConfigSwitchProps {
    task: Task;
    isDisabled: boolean;
    isAutoTrainingEnabled: boolean;
    onAutoTraining: (value: boolean) => void;
}

export const AutoTrainingConfigSwitch: FC<AutoTrainingConfigSwitchProps> = ({
    task,
    isDisabled,
    onAutoTraining,
    isAutoTrainingEnabled,
}) => {
    const onChange = () => {
        onAutoTraining(!isAutoTrainingEnabled);
    };

    return (
        <Flex gap={'size-100'} alignItems={'center'} height='21px'>
            <Switch
                isEmphasized
                justifySelf={'end'}
                aria-label={`Toggle auto training for ${task.title}`}
                isSelected={isAutoTrainingEnabled}
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
