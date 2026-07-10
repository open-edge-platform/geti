// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Pipeline } from '@/api/types';
import { isEmpty } from 'lodash-es';

export const useIsPipelineConfigured = (pipeline?: Pipeline) => {
    if (!pipeline) return false;

    const { model, source } = pipeline;
    const isEditable = !isEmpty(model) && !isEmpty(source);

    return isEditable;
};
