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

import { cloneElement, createContext, ReactChild, ReactElement, ReactNode, useCallback, useContext } from 'react';

import isFunction from 'lodash/isFunction';
import isNumber from 'lodash/isNumber';
import isString from 'lodash/isString';
import isUndefined from 'lodash/isUndefined';
import {
    iNotificationDismiss as DismissOptions,
    iNotification,
    NOTIFICATION_CONTAINER,
    ReactNotifications,
    Store,
} from 'react-notifications-component';

import { MissingProviderError } from '../shared/missing-provider-error';
import { CenterNotificationToast } from './notification-toast/center-notification-toast.component';
import { NotificationToast, NotificationToastProps } from './notification-toast/notification-toast.component';
import { NOTIFICATION_TYPE } from './notification-toast/notification-type.enum';

import classes from './notification.module.scss';

type addToastNotificationProps = Omit<NotificationToastProps, 'remove'> & {
    dismiss?: DismissOptions;
    placement?: NOTIFICATION_CONTAINER;
};

interface addNotificationProps {
    message: ReactChild;
    type: NOTIFICATION_TYPE;
    dismiss?: DismissOptions;
    actionButtons?: ReactElement[];
    onClose?: () => void;
    hasCloseButton?: boolean;
}
interface NotificationContextProps {
    removeNotification: (id: string) => void;
    removeNotifications: () => void;
    addNotification: ({ message, type, dismiss, actionButtons }: addNotificationProps) => string;
    addToastNotification: (data: addToastNotificationProps) => string;
}

interface NotificationProviderProps {
    children: ReactNode;
}

const NotificationContext = createContext<NotificationContextProps | undefined>(undefined);

const DEFAULT_NOTIFICATION_DURATION = 8000;
const DEFAULT_DISMISS_OPTIONS = {
    onScreen: false,
    pauseOnHover: true,
    showIcon: true,
    duration: DEFAULT_NOTIFICATION_DURATION,
};

export const NotificationProvider = ({ children }: NotificationProviderProps): JSX.Element => {
    const removeNotification = (id: string) => {
        Store.removeNotification(id);
    };

    const removeNotifications = () => {
        Store.removeAllNotifications();
    };

    const addNotification = useCallback(
        ({
            type,
            message,
            onClose,
            hasCloseButton = true,
            dismiss = DEFAULT_DISMISS_OPTIONS,
            actionButtons,
        }: addNotificationProps): string => {
            const notificationId = isString(message) || isNumber(message) ? `id-${message}` : `id-${message.key}`;

            const NotificationContainer: iNotification = {
                id: notificationId,
                content: (
                    <CenterNotificationToast
                        type={type}
                        message={message}
                        hasCloseButton={hasCloseButton}
                        actionButtons={actionButtons}
                        cursor={Boolean(dismiss.click) === false ? 'default' : 'pointer'}
                        remove={() => {
                            removeNotification(notificationId);
                            isFunction(onClose) && onClose();
                        }}
                    />
                ),
                message,
                insert: 'top',
                container: 'bottom-center',
                width: 640,
                animationIn: [classes.notification, classes.notificationAnimationFadeIn],
                animationOut: [classes.notification, classes.notificationAnimationFadeOut],
                dismiss: {
                    ...dismiss,
                    // We don't want error notifications to dismiss automatically.
                    // For all the others, we dismiss them after 3 seconds
                    duration:
                        type === NOTIFICATION_TYPE.ERROR
                            ? 0
                            : !isUndefined(dismiss.duration)
                              ? dismiss.duration
                              : DEFAULT_NOTIFICATION_DURATION,
                },
            };

            Store.addNotification(NotificationContainer);

            return notificationId;
        },
        []
    );

    const addToastNotification = useCallback(
        ({
            type,
            title,
            message,
            actionButtons,
            dismiss = DEFAULT_DISMISS_OPTIONS,
            placement = 'bottom-right',
        }: addToastNotificationProps): string => {
            const notificationId = `id-${title ? title : message}`;

            const remove = () => removeNotification(notificationId);
            const enhancedButtons = actionButtons?.map((Component) => cloneElement(Component, { remove }));

            const NotificationContainer: iNotification = {
                id: notificationId,
                content: (
                    <NotificationToast
                        type={type}
                        title={title}
                        remove={remove}
                        message={message}
                        actionButtons={enhancedButtons}
                    />
                ),
                insert: 'top',
                container: placement,
                animationIn: [classes.notification, classes.notificationAnimationFadeIn],
                animationOut: [classes.notification, classes.notificationAnimationFadeOut],
                dismiss: {
                    ...dismiss,
                    // We don't want error notifications to dismiss automatically.
                    // For all the others, we dismiss them after 3 seconds
                    duration: type === NOTIFICATION_TYPE.ERROR ? 0 : DEFAULT_NOTIFICATION_DURATION,
                },
            };

            Store.addNotification(NotificationContainer);

            return notificationId;
        },
        []
    );

    return (
        <NotificationContext.Provider
            value={{ addNotification, addToastNotification, removeNotification, removeNotifications }}
        >
            {children}
        </NotificationContext.Provider>
    );
};

export const Notifications = () => {
    return <ReactNotifications className={classes.notificationContainer} isMobile breakpoint={1024} />;
};

export const useNotification = (): NotificationContextProps => {
    const context = useContext(NotificationContext);

    if (context === undefined) {
        throw new MissingProviderError('useNotification', 'NotificationProvider');
    }

    return context;
};
