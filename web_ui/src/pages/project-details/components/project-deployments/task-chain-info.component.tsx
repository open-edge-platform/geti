// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
