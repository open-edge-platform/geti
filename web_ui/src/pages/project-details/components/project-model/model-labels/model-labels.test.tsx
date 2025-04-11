// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { screen } from '@testing-library/react';

import { Label } from '../../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { projectRender as render } from '../../../../../test-utils/project-provider-render';
import { ModelLabels } from './model-labels.component';

describe('ModelLabels', () => {
    const mockLabels: Label[] = [
        getMockedLabel({ name: 'label-1', id: 'label-1' }),
        getMockedLabel({ name: 'label-2', id: 'label-2' }),
    ];

    it('renders tree view - segmentation', async () => {
        await render(<ModelLabels labels={mockLabels} domain={DOMAIN.SEGMENTATION} />);

        mockLabels.forEach((label) => {
            expect(screen.queryByText(label.name)).toBeInTheDocument();
        });
    });

    it('only renders non empty labels - classification', async () => {
        const mockLabelsWithEmpty: Label[] = [
            getMockedLabel({ name: 'label-1', id: 'label-1' }),
            getMockedLabel({ name: 'label-2', id: 'label-2', parentLabelId: 'label-1' }),
            getMockedLabel({ name: 'label-3', id: 'label-3', isEmpty: true }),
        ];

        await render(<ModelLabels labels={mockLabelsWithEmpty} domain={DOMAIN.CLASSIFICATION} />);

        expect(screen.queryByText(mockLabelsWithEmpty[0].name)).toBeInTheDocument();
        expect(screen.queryByText(mockLabelsWithEmpty[1].name)).toBeInTheDocument();
        expect(screen.queryByText(mockLabelsWithEmpty[2].name)).not.toBeInTheDocument();
    });
});
