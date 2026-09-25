// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { AnnotatorMode } from '../../../../modules/annotator/annotator-mode';

type IsSubmitDisabledParams = {
    mode: AnnotatorMode;
    hasSubsetChanged: boolean;
    isLoadingPredictions: boolean;
    canSubmit: boolean;
    hasInvalidAnnotation: boolean;
    isSaving: boolean;
};

export const getIsSubmitDisabled = ({
    mode,
    hasSubsetChanged,
    isLoadingPredictions,
    canSubmit,
    hasInvalidAnnotation,
    isSaving,
}: IsSubmitDisabledParams): boolean => {
    const isContentSubmittable =
        mode === 'prediction' ? canSubmit : !hasInvalidAnnotation && (canSubmit || hasSubsetChanged);

    return !isContentSubmittable || isSaving || isLoadingPredictions;
};
