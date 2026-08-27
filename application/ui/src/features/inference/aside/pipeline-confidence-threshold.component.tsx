// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { usePatchPipeline, usePipeline } from 'hooks/api/pipeline.hook';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { ConfidenceThreshold } from '../../../components/confidence-threshold/confidence-threshold.component';

export const PipelineConfidenceThreshold = () => {
    const projectId = useProjectIdentifier();
    const { data: pipeline } = usePipeline();
    const updatePipeline = usePatchPipeline();

    const confidenceThreshold = pipeline.inference?.confidence_threshold ?? null;
    const defaultValue = pipeline.model_variant?.optimal_confidence_threshold ?? null;

    if (confidenceThreshold === null || defaultValue === null) {
        return null;
    }

    const handleChange = (value: number) => {
        updatePipeline.mutate({
            params: { path: { project_id: projectId } },
            body: { inference: { confidence_threshold: value } },
        });
    };

    return <ConfidenceThreshold value={confidenceThreshold} defaultValue={defaultValue} onChange={handleChange} />;
};
