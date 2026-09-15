// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactElement, ReactNode } from 'react';

import { ActionButton, Divider, Flex, Text } from '@geti-ui/ui';
import { AcceptCircle, Alert, CloseSmall, CrossCircle, Info } from '@geti-ui/ui/icons';
import { clsx } from 'clsx';
import { isEmpty } from 'lodash-es';
import { toast as sonnerToast, Toaster } from 'sonner';

import { isNonEmptyString } from '../../shared/util';

import classes from './toast.module.scss';

type ToastType = 'success' | 'error' | 'warning' | 'info' | 'neutral';

type ToastProps = {
    id?: string;
    type: ToastType;
    message: ReactNode;
    actionButtons?: ReactElement[];
    duration?: number;
};

const ICON: Record<ToastType, ReactNode> = {
    success: <AcceptCircle className={classes.icon} />,
    error: <CrossCircle className={classes.icon} />,
    warning: <Alert className={classes.icon} />,
    info: <Info className={classes.icon} />,
    neutral: null,
};

// sonner generates a numeric id when none is provided, so it must not be stringified
type CustomToastProps = Pick<ToastProps, 'type' | 'message' | 'actionButtons'> & { id: string | number };

const CustomToast = ({ message, id, actionButtons, type }: CustomToastProps) => {
    const icon = ICON[type];

    return (
        <div aria-label={'toast'} className={clsx(classes[type], classes.toast)}>
            <Flex
                width={'100%'}
                height={'100%'}
                justifyContent={'space-between'}
                alignItems={'center'}
                gap={'size-200'}
            >
                <Flex flex={1} alignItems={'center'} justifyContent={'space-between'}>
                    <Flex gap={'size-100'} alignItems={'center'}>
                        {icon !== null && <Flex>{icon}</Flex>}
                        <Text>{message}</Text>
                    </Flex>

                    {!isEmpty(actionButtons) && (
                        <Flex alignItems={'center'} UNSAFE_className={classes.actionButtons}>
                            {actionButtons}
                        </Flex>
                    )}
                </Flex>

                <Flex height={'100%'} alignItems={'center'} gap={'size-50'}>
                    <Divider
                        orientation={'vertical'}
                        height={'size-400'}
                        size={'M'}
                        UNSAFE_className={classes.toastDivider}
                    />
                    <ActionButton
                        isQuiet
                        onPress={() => sonnerToast.dismiss(id)}
                        aria-label={'Close toast'}
                        UNSAFE_className={classes.closeButton}
                    >
                        <CloseSmall className={classes.icon} />
                    </ActionButton>
                </Flex>
            </Flex>
        </div>
    );
};

const DEFAULT_TOAST_DURATION = 8000;

export const removeToast = (id: string | number) => {
    // sonner dismisses every toast when the id is empty
    if (!id) return;

    sonnerToast.dismiss(id);
};

const parseId = (text: string) => {
    return text.split(' ').join('-').replace(',', '').toLowerCase();
};

export const toast = ({ id, message, actionButtons, type, duration = DEFAULT_TOAST_DURATION }: ToastProps) => {
    // Identical text messages share an id so they replace each other instead of stacking up
    const toastId = id ?? (isNonEmptyString(message) ? `id-${parseId(message)}` : undefined);

    return sonnerToast.custom(
        (currentId) => <CustomToast id={currentId} type={type} message={message} actionButtons={actionButtons} />,
        {
            // An explicit `id: undefined` makes sonner register the toast under a different id
            // than the one handed to the renderer above, which breaks dismissing it
            ...(toastId !== undefined && { id: toastId }),
            // We don't want error notifications to dismiss automatically.
            // For all the others, we dismiss them after {duration}
            duration: type === 'error' ? Infinity : duration,
            className: classes.toastContainer,
        }
    );
};

export const Toast = () => {
    return <Toaster position='bottom-center' className={classes.toaster} />;
};
