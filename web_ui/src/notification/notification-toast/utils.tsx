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

import classes from './notification-toast.module.scss';

export const getTypeToastClass = (type: NOTIFICATION_TYPE): string => {
    switch (type) {
        case NOTIFICATION_TYPE.ERROR:
            return classes['spectrum-Toast--negative'];
        case NOTIFICATION_TYPE.INFO:
            return classes['spectrum-Toast--info'];
        case NOTIFICATION_TYPE.WARNING:
            return classes['spectrum-Toast--warning'];
        default:
            return '';
    }
};

export const getIcon = (type: NOTIFICATION_TYPE): JSX.Element => {
    switch (type) {
        case NOTIFICATION_TYPE.ERROR:
        case NOTIFICATION_TYPE.WARNING:
            return <Alert />;
        case NOTIFICATION_TYPE.INFO:
            return <Info />;
        default:
            return <></>;
    }
};
