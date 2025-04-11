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

import * as path from 'path';

export const resolveTestAssetPath = (...p: string[]) => {
    return path.resolve(__dirname, './../../src/assets/tests-assets/', ...p);
};

export const resolveAntelopePath = () => {
    return resolveTestAssetPath('antelope.png');
};

export const resolveDatasetPath = (...p: string[]) => {
    return path.resolve(__dirname, './../datasets', ...p);
};

export const resolveMockFilesPath = (...p: string[]) => {
    return path.resolve(__dirname, './../mockFiles', ...p);
};
