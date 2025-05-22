// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactElement } from 'react';

import { ActionButton, Flex, Heading, Text } from '@geti/ui';
import { CloseSmall } from '@geti/ui/icons';
import clsx from 'clsx';
import { isEmpty } from 'lodash-es';

import { NOTIFICATION_TYPE } from './notification-type.enum';
import { getIcon, getTypeToastClass } from './utils';

import classes from './notification-toast.module.scss';

export interface NotificationToastProps {
    title?: string;
    message: string;
    type: NOTIFICATION_TYPE;
    actionButtons?: ReactElement[];
    remove: () => void;
}

export const NotificationToast = ({
    type,
    title,
    message,
    actionButtons,
    remove,
}: NotificationToastProps): JSX.Element => {
    const isError = type === NOTIFICATION_TYPE.ERROR;
    const isWarning = type === NOTIFICATION_TYPE.WARNING;

    return (
        <div
            aria-label={'notification toast'}
            className={clsx([
                classes['spectrum-Toast'],
                classes['bottom-right'],
                getTypeToastClass(type),
                classes.toast,
            ])}
        >
            <Flex width={'100%'} direction={'column'}>
                <div
                    className={clsx([
                        classes['spectrum-Toast-content'],
                        { [classes['spectrum-Toast-content--warning']]: isWarning },
                    ])}
                >
                    <Flex columnGap={'size-100'} width={'100%'} direction={'column'}>
                        {!isEmpty(title) && (
                            <Flex alignItems={'center'}>
                                <Heading UNSAFE_className={classes.title}>
                                    {getIcon(type)} {title}
                                </Heading>
                            </Flex>
                        )}

                        <Text id='notification-toast-msg-id' UNSAFE_className={classes.notificationMessage}>
                            {message}
                        </Text>
                    </Flex>
                </div>
                {!isEmpty(actionButtons) && (
                    <Flex marginTop={'size-250'} gap={'size-250'}>
                        {actionButtons}
                    </Flex>
                )}
            </Flex>
            <ActionButton
                isQuiet
                onPress={remove}
                aria-label='close notification'
                UNSAFE_className={clsx([
                    classes['spectrum-Toast-buttons'],
                    {
                        [classes['spectrum-Toast-buttons--warning']]: isWarning,
                        [classes['spectrum-Toast-buttons--negative']]: isError,
                    },
                ])}
            >
                <CloseSmall
                    aria-label='close notification icon'
                    className={isWarning ? classes['close-notification-icon--warning'] : ''}
                />
            </ActionButton>
        </div>
    );
};
