// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { ModelArchitecture as ModelArchitectureType } from '@/api/types';
import { useTranslation } from 'react-i18next';

import { ModelArchitecture } from './model-architecture.component';
import { ModelArchitecturesListLayout } from './model-architectures-list-layout/model-architectures-list-layout.component';

type RecommendedModelArchitecturesProps = {
    modelArchitectures: ModelArchitectureType[];
    selectedModelArchitectureId: string | null;
    onSelectedModelArchitectureIdChange: (modelArchitectureId: string | null) => void;
};

export const RecommendedModelArchitectures = ({
    modelArchitectures,
    onSelectedModelArchitectureIdChange,
    selectedModelArchitectureId,
}: RecommendedModelArchitecturesProps) => {
    const { t } = useTranslation();
    return (
        <ModelArchitecturesListLayout
            selectedModelArchitectureId={selectedModelArchitectureId}
            onSelectedModelArchitectureIdChange={onSelectedModelArchitectureIdChange}
            ariaLabel={t('models.recommendedArchitecturesAria')}
        >
            {modelArchitectures.map((modelArchitecture) => (
                <ModelArchitecture
                    key={modelArchitecture.id}
                    modelArchitecture={modelArchitecture}
                    selectedModelArchitectureId={selectedModelArchitectureId}
                    onSelectedModelArchitectureIdChange={onSelectedModelArchitectureIdChange}
                />
            ))}
        </ModelArchitecturesListLayout>
    );
};
