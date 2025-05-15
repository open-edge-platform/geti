// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { negate } from 'lodash-es';

import { OptimizedModel } from '../../../../../../core/models/optimized-models.interface';

export const isBaselineModel = (model: OptimizedModel) =>
    model.precision.includes('FP32') && model.optimizationType === 'MO';

export const isNotBaselineModel = negate(isBaselineModel);
