// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useAnnotationActions } from '../../../../shared/annotator/annotation-actions-provider.component';
import type { AnnotatorMode } from '../../../../shared/annotator/annotator-mode';

type UseIsSubmitDisabledParams = {
    mode: AnnotatorMode;
    hasSubsetChanged: boolean;
    isLoadingPredictions: boolean;
};

export const useIsSubmitDisabled = ({
    mode,
    hasSubsetChanged,
    isLoadingPredictions,
}: UseIsSubmitDisabledParams): boolean => {
    const { canSubmit, hasInvalidAnnotation, isSaving } = useAnnotationActions();

    const isContentSubmittable =
        mode === 'prediction' ? canSubmit : !hasInvalidAnnotation && (canSubmit || hasSubsetChanged);

    return !isContentSubmittable || isSaving || isLoadingPredictions;
};
