// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { paths } from '../../../../../../core/services/routes';

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
