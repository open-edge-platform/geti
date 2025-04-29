// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text, View } from '@adobe/react-spectrum';

import classes from './project-deployments.module.scss';

interface TaskChainInfoProps {
    taskName: string;
    taskIndex: number;
}

export const TaskChainInfo = ({ taskName, taskIndex }: TaskChainInfoProps) => {
    return (
        <Flex direction={'column'}>
            <Flex justifyContent={'space-between'} alignItems={'center'} marginBottom={'size-100'}>
                <Text UNSAFE_className={classes.headerInfo} id={'task-chain-info-header-id'}>
                    Task chain - {taskName}
                </Text>
                <Text UNSAFE_className={classes.label} id={'task-chain-info-label-id'}>
                    {taskIndex + 1} of 2
                </Text>
            </Flex>

            <Text UNSAFE_className={classes.label}>Computer vision task</Text>

            <View UNSAFE_className={classes.taskInfoWrapper}>
                <Text UNSAFE_className={classes.taskTitle} id={'task-chain-label-title-id'}>
                    {taskName}
                </Text>
            </View>
        </Flex>
    );
};
