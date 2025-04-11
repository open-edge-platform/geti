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

import { TestScore } from '../../../../core/tests/tests.interface';

export const THRESHOLD_TOOLTIP =
    'Model score for every image is calculated by comparing model predictions with user annotation for this image';

export const THRESHOLD_LABEL_TOOLTIP = (name: string) =>
    // eslint-disable-next-line max-len
    `Model score for every image is calculated by comparing label '${name}' model predictions with label '${name}' user annotation for image`;

export const SCORE_FORMATTER_OPTIONS: Intl.NumberFormatOptions = { style: 'percent', maximumFractionDigits: 0 };

export const isEqualLabelId =
    (selectedLabelId: string) =>
    ({ labelId }: TestScore) =>
        String(labelId) === selectedLabelId;
