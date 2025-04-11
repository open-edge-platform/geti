// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.
export const DEFAULT_PERFORMANCE_TOOLTIP_MESSAGE = 'Latest model score';

export const ANOMALY_IMAGE_PERFORMANCE_TOOLTIP_MESSAGE =
    'This score reflects how good the model is in distinguishing normal vs. anomalous images';

export const ANOMALY_OBJECT_PERFORMANCE_TOOLTIP_MESSAGE =
    'This score reflects how good the model is in localizing the anomalous objects inside the anomalous images';

export const ANOMALY_OBJECT_PERFORMANCE_N_A_TOOLTIP_MESSAGE = 'Annotate your media to compute localization score';

export const ACTIVATED_MODEL_MESSAGE = (modelName: string, version: number) =>
    `You have changed the active model to ${modelName} Version ${version}`;
