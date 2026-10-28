// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useIntelligentScissorsWorker } from '../../../shared/smart-tools/use-intelligent-scissors-worker.hook';
import { useSegmentAnythingWorker } from '../../../shared/smart-tools/use-segment-anything-worker.hook';
import { useSSIMWorker } from '../../../shared/smart-tools/use-ssim-worker.hook';
import { useAvailableTools } from './annotator-tools/use-available-tools';

/**
 * Eagerly boot the annotator-tool web workers (SAM, SSIM, magnetic-lasso) as
 * soon as the annotator mounts, so the heavy WASM + ONNX init runs in the
 * background and the corresponding tools are responsive the moment the user
 * picks them.
 */
export const usePreloadWebworkers = () => {
    const availableTools = useAvailableTools();
    const tools = new Set(availableTools.map((tool) => tool.type));

    useSegmentAnythingWorker(tools.has('sam'));
    useSSIMWorker(tools.has('ssim'));
    useIntelligentScissorsWorker(tools.has('magnetic-lasso'));
};
