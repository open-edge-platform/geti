// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

import { Flex, Link, Text } from '@adobe/react-spectrum';
import { createPortal } from 'react-dom';

import { CloseSmall, Info } from '../../../../../assets/icons';
import {
    ColorMode,
    QuietActionButton,
} from '../../../../../shared/components/quiet-button/quiet-action-button.component';
import { useShouldShowEmptyAnnotationsWarning } from '../../../hooks/use-should-show-empty-annotations-warning.hook';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { NOTIFICATION_MESSAGE } from '../utils';

import classes from './annotation-list-thumbnail-grid.module.scss';

export const EmptyAnnotationsNotification = (): JSX.Element => {
    const { previousTask, selectedTask, setSelectedTask } = useTask();
    const shouldShowEmptyAnnotationsWarning = useShouldShowEmptyAnnotationsWarning();

    const [isVisible, setIsVisible] = useState<boolean>(shouldShowEmptyAnnotationsWarning);

    const handleSelectPreviousTask = () => {
        setSelectedTask(previousTask ?? null);
    };

    useEffect(() => {
        setIsVisible(shouldShowEmptyAnnotationsWarning);
    }, [selectedTask, shouldShowEmptyAnnotationsWarning]);

    return isVisible && selectedTask !== null ? (
        createPortal(
            <Flex
                position={'fixed'}
                zIndex={9999999}
                bottom={'size-600'}
                width={'100%'}
                alignItems={'center'}
                justifyContent={'center'}
            >
                <Flex
                    UNSAFE_className={classes.emptyAnnotationsNotification}
                    alignItems={'center'}
                    justifyContent={'space-between'}
                >
                    <Flex gap={'size-250'} alignItems={'center'}>
                        <Info />
                        <Text>{NOTIFICATION_MESSAGE[selectedTask.domain]}</Text>
                        <Link variant={'secondary'} onPress={handleSelectPreviousTask}>
                            Go to detection
                        </Link>
                    </Flex>
                    <QuietActionButton colorMode={ColorMode.LIGHT} onPress={() => setIsVisible(false)}>
                        <CloseSmall />
                    </QuietActionButton>
                </Flex>
            </Flex>,

            document.getElementById('custom-notification') as Element
        )
    ) : (
        <></>
    );
};
