// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties, ReactChild, ReactElement } from 'react';

import { Flex, Text } from '@geti/ui';
import clsx from 'clsx';
import { isEmpty, isString } from 'lodash-es';
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
