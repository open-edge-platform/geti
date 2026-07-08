// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { View } from '@geti-ui/ui';

import { PipelineHealth } from './pipeline-health.component';

export const Footer = () => {
    return (
        <View backgroundColor={'gray-100'} paddingY={'size-150'} paddingX={'size-300'}>
            <PipelineHealth />
        </View>
    );
};
