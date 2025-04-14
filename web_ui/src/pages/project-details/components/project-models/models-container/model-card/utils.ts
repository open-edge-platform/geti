// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
export const DEFAULT_PERFORMANCE_TOOLTIP_MESSAGE = 'Latest model score';

export const ANOMALY_IMAGE_PERFORMANCE_TOOLTIP_MESSAGE =
    'This score reflects how good the model is in distinguishing normal vs. anomalous images';

export const ANOMALY_OBJECT_PERFORMANCE_TOOLTIP_MESSAGE =
    'This score reflects how good the model is in localizing the anomalous objects inside the anomalous images';

export const ANOMALY_OBJECT_PERFORMANCE_N_A_TOOLTIP_MESSAGE = 'Annotate your media to compute localization score';

export const ACTIVATED_MODEL_MESSAGE = (modelName: string, version: number) =>
    `You have changed the active model to ${modelName} Version ${version}`;
