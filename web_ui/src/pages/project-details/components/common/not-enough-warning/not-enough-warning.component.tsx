// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, ReactNode } from 'react';

import { View } from '@adobe/react-spectrum';

import classes from './not-enough-warning.module.scss';

interface NotEnoughWarningProps {
    children: ReactNode;
}

export const NotEnoughWarning: FC<NotEnoughWarningProps> = ({ children }) => {
    return <View UNSAFE_className={classes.warningContainer}>{children}</View>;
};
