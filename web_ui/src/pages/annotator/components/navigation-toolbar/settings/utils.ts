// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isObject from 'lodash/isObject';

import { AnnotatorSettingsConfig, FEATURES_KEYS } from '../../../../../core/user-settings/dtos/user-settings.interface';

export const containsFeatureConfig = (config: unknown): config is AnnotatorSettingsConfig => {
    return isObject(config) && config.hasOwnProperty(FEATURES_KEYS.ANNOTATION_PANEL);
};
