// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactNode } from 'react';

import { View } from '@geti-ui/ui';

import classes from './edit-source.module.scss';

interface EditSourceFieldsPanelProps {
    children: ReactNode;
}

export const EditSourceFieldsPanel = ({ children }: EditSourceFieldsPanelProps) => {
    return <View UNSAFE_className={classes.container}>{children}</View>;
};
