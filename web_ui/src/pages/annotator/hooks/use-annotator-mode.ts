// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useSearchParams } from 'react-router-dom';

import { ANNOTATOR_MODE } from '../core/annotation-tool-context.interface';

export const useAnnotatorMode = () => {
    const [searchParams] = useSearchParams();
    const paramMode = searchParams.get('mode') ?? ANNOTATOR_MODE.ACTIVE_LEARNING;
    const currentMode =
        paramMode === ANNOTATOR_MODE.ACTIVE_LEARNING ? ANNOTATOR_MODE.ACTIVE_LEARNING : ANNOTATOR_MODE.PREDICTION;
    const isActiveLearningMode = currentMode === ANNOTATOR_MODE.ACTIVE_LEARNING;

    return { isActiveLearningMode, currentMode };
};
