// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
