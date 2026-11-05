// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactNode } from 'react';

import { View } from '@geti-ui/ui';

import classes from './edit-sink.module.scss';

interface EditSinkFieldsPanelProps {
    children: ReactNode;
}

export const EditSinkFieldsPanel = ({ children }: EditSinkFieldsPanelProps) => {
    return <View UNSAFE_className={classes.container}>{children}</View>;
};
