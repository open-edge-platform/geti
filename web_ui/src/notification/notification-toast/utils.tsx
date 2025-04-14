// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
