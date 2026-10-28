// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { ModelArchitectureWithPerformanceCategory } from '@/api/types';

import { ModelArchitectureCard } from './model-architecture-card/model-architecture-card.component';

type ModelArchitectureProps = {
    modelArchitecture: ModelArchitectureWithPerformanceCategory;
    selectedModelArchitectureId: string | null;
    onSelectedModelArchitectureIdChange: (modelArchitectureId: string | null) => void;
};

export const ModelArchitecture = ({
    modelArchitecture,
    selectedModelArchitectureId,
    onSelectedModelArchitectureIdChange,
}: ModelArchitectureProps) => {
    const isSelected = modelArchitecture.id === selectedModelArchitectureId;

    return (
        <ModelArchitectureCard
            modelArchitecture={modelArchitecture}
            isSelected={isSelected}
            onSelect={() => onSelectedModelArchitectureIdChange(modelArchitecture.id)}
        >
            <ModelArchitectureCard.Name />
            <ModelArchitectureCard.Parameters />
            <ModelArchitectureCard.PerformanceCategoryBadge />
        </ModelArchitectureCard>
    );
};
