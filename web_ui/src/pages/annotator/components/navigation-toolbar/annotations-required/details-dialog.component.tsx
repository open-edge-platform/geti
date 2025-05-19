// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Fragment } from 'react';

import { Content, Dialog, Divider, Flex, Text, View } from '@geti/ui';
import { isEmpty } from 'lodash-es';

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
