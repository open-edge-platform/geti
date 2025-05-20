// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Alert, Info } from '@geti/ui/icons';

import { NOTIFICATION_TYPE } from './notification-type.enum';
import { getIcon, getTypeToastClass } from './utils';

describe('Notification toast utils', () => {
    describe('getTypeToastClass function', () => {
        it('Check if information notification returns info class', () => {
            const notificationInfoClass = getTypeToastClass(NOTIFICATION_TYPE.INFO);
            expect(notificationInfoClass).toMatch(/--info/);
        });

        it('Check if error notification returns negative class', () => {
            const notificationInfoClass = getTypeToastClass(NOTIFICATION_TYPE.ERROR);
            expect(notificationInfoClass).toMatch(/--negative/);
        });
        it('Check if warning notification returns warning class', () => {
            const notificationInfoClass = getTypeToastClass(NOTIFICATION_TYPE.WARNING);
            expect(notificationInfoClass).toMatch(/--warning/);
        });

        it('Check if default notification returns no additional class', () => {
            const notificationInfoClass = getTypeToastClass(NOTIFICATION_TYPE.DEFAULT);
            expect(notificationInfoClass).toBe('');
        });
    });

    describe('getIcon function', () => {
        it('Check if error notification return alert icon', () => {
            const icon = getIcon(NOTIFICATION_TYPE.ERROR);
            expect(icon).toStrictEqual(<Alert />);
        });

        it('Check if information notification return info icon', () => {
            const icon = getIcon(NOTIFICATION_TYPE.INFO);
            expect(icon).toStrictEqual(<Info />);
        });

        it('Check if default notification do not return icon', () => {
            const icon = getIcon(NOTIFICATION_TYPE.DEFAULT);
            expect(icon).toStrictEqual(<></>);
        });
    });
});
