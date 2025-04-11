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

import { Alert, Info } from '../../assets/icons';
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
