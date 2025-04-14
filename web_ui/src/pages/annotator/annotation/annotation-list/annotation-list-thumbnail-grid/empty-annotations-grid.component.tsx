// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Link, Text, View } from '@adobe/react-spectrum';

import { Info } from '../../../../../assets/icons';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { NOTIFICATION_MESSAGE } from '../utils';

export const EmptyAnnotationsGrid = (): JSX.Element => {
    const { setSelectedTask, previousTask, selectedTask } = useTask();

    const handleSelectPreviousTask = () => {
        setSelectedTask(previousTask ?? null);
    };

    return selectedTask !== null ? (
        <View marginTop='size-200'>
            <Flex>
                <View paddingX='size-100' paddingTop={'size-25'}>
                    <Info />
                </View>
                <Flex direction='column' gap={'size-75'}>
                    <Text>{NOTIFICATION_MESSAGE[selectedTask.domain]}</Text>
                    <Text>
                        Please select the{' '}
                        <Link variant='overBackground' onPress={handleSelectPreviousTask}>
                            previous task
                        </Link>{' '}
                        to add objects.
                    </Text>
                </Flex>
            </Flex>
        </View>
    ) : (
        <></>
    );
};
