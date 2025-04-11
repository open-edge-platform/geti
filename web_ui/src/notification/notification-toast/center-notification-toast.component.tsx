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

import { CSSProperties, ReactChild, ReactElement } from 'react';

import { Flex, Text } from '@adobe/react-spectrum';
import clsx from 'clsx';
import isEmpty from 'lodash/isEmpty';
import isString from 'lodash/isString';
import { useId } from 'react-aria';

import { CloseSmall } from '../../assets/icons';
import { Divider } from '../../shared/components/divider/divider.component';
import { QuietActionButton } from '../../shared/components/quiet-button/quiet-action-button.component';
import { NOTIFICATION_TYPE } from './notification-type.enum';
import { getIcon, getTypeToastClass } from './utils';

import classes from './notification-toast.module.scss';

interface CenterNotificationToastProps {
    type: NOTIFICATION_TYPE;
    remove: () => void;
    message: ReactChild;
    hasCloseButton: boolean;
    cursor?: CSSProperties['cursor'];
    actionButtons?: ReactElement[];
}

export const CenterNotificationToast = ({
    type,
    message,
    remove,
    hasCloseButton,
    actionButtons,
    cursor = 'pointer',
}: CenterNotificationToastProps): JSX.Element => {
    const id = useId();
    const isError = type === NOTIFICATION_TYPE.ERROR;
    const isWarning = type === NOTIFICATION_TYPE.WARNING;

    return (
        <div
            aria-label={'notification toast'}
            className={clsx([classes['spectrum-Toast'], getTypeToastClass(type), classes.toast])}
            style={{ cursor }}
        >
            <Flex width={'100%'} alignItems={'center'} justifyContent={'space-between'}>
                <div
                    className={clsx([
                        classes['spectrum-Toast-content'],
                        { [classes['spectrum-Toast-content--warning']]: isWarning },
                    ])}
                >
                    {isString(message) ? (
                        <Flex columnGap={'size-100'} alignItems={'center'}>
                            <Flex alignItems={'center'}>{getIcon(type)}</Flex>
                            <Text
                                id={`notification-msg-${type}-${id}-id`}
                                UNSAFE_className={classes.notificationMessage}
                            >
                                {message}
                            </Text>
                        </Flex>
                    ) : (
                        message
                    )}
                </div>
                {!isEmpty(actionButtons) && (
                    <Flex
                        justifyContent={'end'}
                        alignItems={'center'}
                        UNSAFE_className={classes['spectrum-Toast-buttons']}
                    >
                        {actionButtons}
                    </Flex>
                )}
            </Flex>

            {hasCloseButton && (
                <>
                    <Divider orientation='vertical' size='S' UNSAFE_className={classes.notificationToastDivider} />
                    <QuietActionButton
                        onPress={remove}
                        alignSelf={'center'}
                        aria-label={'close notification'}
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
                    </QuietActionButton>
                </>
            )}
        </div>
    );
};
