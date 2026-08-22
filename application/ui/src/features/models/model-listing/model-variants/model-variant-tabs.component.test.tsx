// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen } from '@testing-library/react';
import { getMockedModel } from 'mocks/mock-model';
import { getMockedVariant } from 'mocks/mock-model-variant';
import { render } from 'test-utils/render';

import { ModelVariantsTabs } from './model-variant-tabs.component';

describe('ModelVariantsTabs', () => {
    it('shows a placeholder when the model has no variants', () => {
        render(<ModelVariantsTabs model={getMockedModel({ variants: [] })} />);

        expect(screen.getByText('No available model variants.')).toBeInTheDocument();
    });

    it('keeps rendering the variants and disables quantization once the weights are deleted', () => {
        const model = getMockedModel({
            files_deleted: true,
            variants: [getMockedVariant({ id: 'ov-1', format: 'openvino', precision: 'fp16', weights_size: 0 })],
        });

        render(<ModelVariantsTabs model={model} />);

        expect(screen.queryByText('No available model variants.')).not.toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Download model ov-1' })).toBeDisabled();
        expect(screen.getByRole('button', { name: 'Start quantization' })).toBeDisabled();
    });
});
