// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { ModelArchitectureWithPerformanceCategory } from '@/api/types';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { getMockedModelArchitecture } from 'mocks/mock-model';
import { render } from 'test-utils/render';

import { ModelArchitecture } from './model-architecture.component';
import { ModelArchitecturesListLayout } from './model-architectures-list-layout/model-architectures-list-layout.component';

type OnSelectedModelArchitectureIdChange = (modelArchitectureId: string | null) => void;

const renderModelArchitecture = ({
    selectedModelArchitectureId = null,
    onSelectedModelArchitectureIdChange = rs.fn<OnSelectedModelArchitectureIdChange>(),
    modelArchitecture = getMockedModelArchitecture(),
}: {
    selectedModelArchitectureId?: string | null;
    onSelectedModelArchitectureIdChange?: OnSelectedModelArchitectureIdChange;
    modelArchitecture?: ModelArchitectureWithPerformanceCategory;
} = {}) => {
    render(
        <ModelArchitecturesListLayout
            selectedModelArchitectureId={selectedModelArchitectureId}
            onSelectedModelArchitectureIdChange={onSelectedModelArchitectureIdChange}
            ariaLabel={'Model architectures'}
        >
            <ModelArchitecture
                modelArchitecture={modelArchitecture}
                selectedModelArchitectureId={selectedModelArchitectureId}
                onSelectedModelArchitectureIdChange={onSelectedModelArchitectureIdChange}
            />
        </ModelArchitecturesListLayout>
    );

    return { modelArchitecture };
};

describe('ModelArchitecture', () => {
    it('renders the model architecture name and number of parameters', () => {
        const modelArchitecture = getMockedModelArchitecture({ name: 'Deim-DFine-L' });
        renderModelArchitecture({ modelArchitecture });

        expect(screen.getByText(modelArchitecture.name)).toBeVisible();
        expect(
            screen.getByText(`Number of parameters: ${modelArchitecture.stats?.trainable_parameters} million`)
        ).toBeVisible();
    });

    it.each([
        ['speed', 'Speed'],
        ['balance', 'Balance'],
        ['accuracy', 'Accuracy'],
    ])('renders the %s performance category badge for top picks', (performanceCategory, label) => {
        renderModelArchitecture({ modelArchitecture: getMockedModelArchitecture({ performanceCategory }) });

        expect(screen.getByText(label)).toBeVisible();
    });

    it('does not render a performance category badge for other architectures', () => {
        renderModelArchitecture({ modelArchitecture: getMockedModelArchitecture({ performanceCategory: undefined }) });

        expect(screen.queryByText(/^(speed|balance|accuracy)$/i)).not.toBeInTheDocument();
    });

    it('calls onSelectedModelArchitectureIdChange with the architecture id when clicked', async () => {
        const user = userEvent.setup();
        const onSelectedModelArchitectureIdChange = rs.fn();

        renderModelArchitecture({ onSelectedModelArchitectureIdChange });

        await user.click(screen.getByText('Deim-DFine-L'));

        expect(onSelectedModelArchitectureIdChange).toHaveBeenCalledWith('Object_Detection_Deim_DFine_L');
    });

    it('renders the radio button as selected when selectedModelArchitectureId matches', () => {
        renderModelArchitecture({
            selectedModelArchitectureId: 'Object_Detection_Deim_DFine_L',
            modelArchitecture: getMockedModelArchitecture({ id: 'Object_Detection_Deim_DFine_L' }),
        });

        expect(screen.getByRole('radio', { name: 'Deim-DFine-L' })).toBeChecked();
    });

    it('renders the radio button as not selected when selectedModelArchitectureId does not match', () => {
        renderModelArchitecture({
            selectedModelArchitectureId: 'some-other-id',
            modelArchitecture: getMockedModelArchitecture({ id: 'Object_Detection_Deim_DFine_L' }),
        });

        expect(screen.getByRole('radio', { name: 'Deim-DFine-L' })).not.toBeChecked();
    });

    it('renders the radio button as not selected when selectedModelArchitectureId is null', () => {
        renderModelArchitecture({ selectedModelArchitectureId: null });

        expect(screen.getByRole('radio', { name: 'Deim-DFine-L' })).not.toBeChecked();
    });

    describe('benchmark stats', () => {
        const detectionArchitecture = getMockedModelArchitecture({
            task: 'detection',
            stats: {
                gigaflops: 91,
                trainable_parameters: 31,
                benchmark_metrics: {
                    imagenet_top1_accuracy: null,
                    imagenet_top5_accuracy: null,
                    coco_map_50_95: 55.3,
                    coco_map_50: null,
                },
            },
        });

        it('shows gigaflops and mAP', () => {
            renderModelArchitecture({ modelArchitecture: detectionArchitecture });

            expect(screen.getByText(`Gigaflops: ${detectionArchitecture.stats?.gigaflops}`)).toBeVisible();
            expect(screen.getByText('mAP on COCO: 55.3%')).toBeVisible();
        });

        it('shows Top-1 Acc for classification tasks', () => {
            const classificationArchitecture = getMockedModelArchitecture({
                task: 'classification',
                stats: {
                    gigaflops: 2,
                    trainable_parameters: 5,
                    benchmark_metrics: {
                        imagenet_top1_accuracy: 76.2,
                        imagenet_top5_accuracy: 95.3,
                        coco_map_50_95: null,
                        coco_map_50: null,
                    },
                },
            });

            renderModelArchitecture({ modelArchitecture: classificationArchitecture });

            expect(screen.getByText('Top-1 Acc on ImageNet: 76.2%')).toBeVisible();
        });
    });
});
