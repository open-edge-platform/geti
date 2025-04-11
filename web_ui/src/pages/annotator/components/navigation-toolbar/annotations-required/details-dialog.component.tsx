// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Fragment } from 'react';

import { Content, Dialog, Divider, Flex, Text, View } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

import { RequiredAnnotationsDetailsEntry } from '../../../../../core/projects/project-status.interface';
import { TaskRequiredAnnotations } from '../../../hooks/use-required-annotations.hook';

import classes from './annotations-required.module.scss';

interface DetailsDialogProps {
    clientWidth: number;
    isAutoTrainingOn: boolean;
    requiredAnnotations: TaskRequiredAnnotations[];
}

export const DetailsDialog = ({
    requiredAnnotations,
    clientWidth,
    isAutoTrainingOn,
}: DetailsDialogProps): JSX.Element => {
    return (
        <Dialog width='100%' minWidth={clientWidth} UNSAFE_className={classes.dialog}>
            <Content UNSAFE_style={{ flex: 1 }}>
                {requiredAnnotations.map((task, taskIndex) => {
                    const hasDetails = !isEmpty(task.details);
                    const value = isAutoTrainingOn ? task.value : task.newAnnotations;

                    return (
                        <Fragment key={`task-${task.title}-${taskIndex}`}>
                            {taskIndex >= 1 ? <Divider size='S' UNSAFE_className={classes.divider} /> : null}

                            <Flex alignItems={'center'} justifyContent={'space-between'}>
                                <Text>{task.title}</Text>
                                {!hasDetails ? <Text>{value}</Text> : <></>}
                            </Flex>

                            {task.details.map((detailsEntry: RequiredAnnotationsDetailsEntry) => (
                                <Flex
                                    gap='size-500'
                                    alignItems='center'
                                    justifyContent='space-between'
                                    key={detailsEntry.id}
                                >
                                    <Flex alignItems='center'>
                                        <View
                                            width='size-100'
                                            height='size-100'
                                            marginEnd='size-150'
                                            borderRadius='large'
                                            UNSAFE_style={{ backgroundColor: detailsEntry.color }}
                                        />
                                        <Text>{detailsEntry.name}</Text>
                                    </Flex>
                                    <Text>{detailsEntry.value}</Text>
                                </Flex>
                            ))}
                        </Fragment>
                    );
                })}
            </Content>
        </Dialog>
    );
};
