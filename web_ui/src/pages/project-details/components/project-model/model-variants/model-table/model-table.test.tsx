// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Cell } from '@adobe/react-spectrum';
import { screen } from '@testing-library/react';

import { ModelFormat } from '../../../../../../core/models/dtos/model-details.interface';
import { OptimizedModel } from '../../../../../../core/models/optimized-models.interface';
import { LifecycleStage } from '../../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { projectRender as render } from '../../../../../../test-utils/project-provider-render';
import { ModelTableColumnKeys } from '../utils';
import { ModelTable } from './model-table.component';

const mockedModel: OptimizedModel = {
    id: '123',
    version: 1,
    precision: ['FP32'],
    configurations: [],
    modelName: 'ATSS OpenVINO',
    modelStatus: 'SUCCESS',
    creationDate: '2023-03-22T08:39:35.532000+00:00',
    previousRevisionId: '641abec79cc05824cf4a9961',
    optimizationMethods: [],
    optimizationObjectives: {},
    previousTrainedRevisionId: '641abec79cc05824cf4a9961',
    optimizationType: 'MO',
    accuracy: 0.4,
    modelSize: '9.97 MB',
    labels: [],
    hasExplainableAI: false,
    modelFormat: ModelFormat.OpenVINO,
    license: 'Apache 2.0',
    lifecycleStage: LifecycleStage.ACTIVE,
};

describe('ModelTable', () => {
    it('renders empty', async () => {
        await render(<ModelTable data={[]} columns={[]} />);

        expect(screen.queryByRole('heading')).not.toBeInTheDocument();
        expect(screen.queryByRole('rowheader')).not.toBeInTheDocument();
    });

    it('renders empty model message', async () => {
        const emptyModelMessage = 'test message';
        await render(<ModelTable data={[]} columns={[]} emptyModelMessage={emptyModelMessage} />);

        const heading = screen.getByRole('heading');
        expect(heading).toBeVisible();
        expect(heading).toHaveTextContent(emptyModelMessage);
        expect(screen.queryByRole('rowheader')).not.toBeInTheDocument();
    });

    it('renders table', async () => {
        const modelNameColumn = {
            width: 50,
            label: 'BASELINE MODELS',
            dataKey: ModelTableColumnKeys.MODEL_NAME,
            component: () => <Cell key={ModelTableColumnKeys.MODEL_NAME}>{ModelTableColumnKeys.MODEL_NAME}</Cell>,
        };
        const modelSizeColumn = {
            width: 12,
            label: 'SIZE',
            dataKey: ModelTableColumnKeys.MODEL_SIZE,
            component: () => <Cell key={ModelTableColumnKeys.MODEL_SIZE}>{ModelTableColumnKeys.MODEL_SIZE}</Cell>,
        };
        await render(<ModelTable data={[mockedModel]} columns={[modelNameColumn, modelSizeColumn]} />);

        expect(screen.getByRole('rowheader', { name: modelNameColumn.dataKey })).toBeVisible();
        expect(screen.getByRole('columnheader', { name: modelNameColumn.label })).toBeVisible();

        expect(screen.getByRole('gridcell', { name: modelSizeColumn.dataKey })).toBeVisible();
        expect(screen.getByRole('columnheader', { name: modelSizeColumn.label })).toBeVisible();
    });
});
