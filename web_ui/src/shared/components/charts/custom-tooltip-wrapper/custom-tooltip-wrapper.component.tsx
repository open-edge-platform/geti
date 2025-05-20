// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { View } from '@geti/ui';

import classes from './custom-tooltip-wrapper.module.scss';

interface CustomTooltipWrapperProps {
    children: ReactNode;
}

export const CustomTooltipWrapper = ({ children }: CustomTooltipWrapperProps): JSX.Element => {
    return <View UNSAFE_className={classes.customTooltipWrapper}>{children}</View>;
};
