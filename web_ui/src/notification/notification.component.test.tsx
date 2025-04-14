// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useEffect } from 'react';

import { render, screen } from '@testing-library/react';

import { NOTIFICATION_TYPE } from './notification-toast/notification-type.enum';
import { NotificationProvider, Notifications, useNotification } from './notification.component';

type Notification = Parameters<ReturnType<typeof useNotification>['addNotification']>[0];

const Wrapper = ({ children }: { children: ReactNode }) => {
    return (
        <NotificationProvider>
            <Notifications />
            {children}
        </NotificationProvider>
    );
};

const App = ({ notification }: { notification: Notification }) => {
    const { addNotification } = useNotification();

    useEffect(() => {
        addNotification(notification);
    }, [addNotification, notification]);

    return null;
};

describe('addNotification', () => {
    it('should add a notification and return the notificationId', async () => {
        render(<App notification={{ message: 'Test notification', type: NOTIFICATION_TYPE.INFO }} />, {
            wrapper: Wrapper,
        });

        expect(await screen.findByText('Test notification')).toBeVisible();
    });

    it('should add notification with custom buttons', async () => {
        render(
            <App
                notification={{
                    message: 'Test notification',
                    type: NOTIFICATION_TYPE.INFO,
                    actionButtons: [<button key='button'>test button</button>],
                }}
            />,
            {
                wrapper: Wrapper,
            }
        );

        expect(await screen.findByText('Test notification')).toBeVisible();
        expect(screen.getByRole('button', { name: 'test button' })).toBeVisible();
    });
});
