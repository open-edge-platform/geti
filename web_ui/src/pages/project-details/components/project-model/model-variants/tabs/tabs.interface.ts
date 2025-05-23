// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core/src/services/routes';

export enum ModelVariantTabsKeys {
    OPENVINO = 'openvino',
    PYTORCH = 'pytorch',
    ONNX = 'onnx',
}

export const MODEL_TABS_TO_PATH = {
    [ModelVariantTabsKeys.ONNX]: paths.project.models.model.modelVariants.onnx,
    [ModelVariantTabsKeys.PYTORCH]: paths.project.models.model.modelVariants.pytorch,
    [ModelVariantTabsKeys.OPENVINO]: paths.project.models.model.modelVariants.openVino,
};
