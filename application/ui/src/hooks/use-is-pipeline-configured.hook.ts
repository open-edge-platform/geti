// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { isEmpty } from 'lodash-es';

import type { Pipeline } from '../api/shared-types';

export const useIsPipelineConfigured = (pipeline?: Pipeline) => {
    if (!pipeline) return false;

    const { model, source } = pipeline;
    const isEditable = !isEmpty(model) && !isEmpty(source);

    return isEditable;
};
