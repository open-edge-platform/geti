// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
