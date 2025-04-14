// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { TrainedModel } from '../../../../../../core/models/optimized-models.interface';
import { getMockedOptimizedModel } from '../../../../../../test-utils/mocked-items-factory/mocked-model';
import { projectRender as render } from '../../../../../../test-utils/project-provider-render';
import { ModelTableNameCell } from './model-table-name-cell.component';

const mockedModel = getMockedOptimizedModel();

const { hasExplainableAI, optimizationType, ...model } = mockedModel;
const mockedTrainedModel: TrainedModel = {
    ...model,
    isLabelSchemaUpToDate: false,
    numberOfFrames: 1,
    numberOfImages: 1,
    numberOfSamples: 1,
    architecture: '123',
    totalDiskSize: '10 MB',
};

describe('ModelTableNameCell', () => {
    const description = 'test description';

    it('explanation includes and default description', async () => {
        await render(
            <ModelTableNameCell row={{ ...mockedModel, hasExplainableAI: true }} defaultDescription={description} />
        );

        expect(screen.getByText(`${description} (Explanation included)`)).toBeVisible();
        expect(screen.getByText(`${mockedModel.modelName} (Explanation included)`)).toBeVisible();
    });

    it('Post-training optimization description', async () => {
        await render(
            <ModelTableNameCell row={{ ...mockedModel, optimizationType: 'POT' }} defaultDescription={description} />
        );

        expect(screen.getByText(mockedModel.modelName)).toBeVisible();
        expect(screen.getByText('Post-training optimization')).toBeVisible();
    });

    it('trained model', async () => {
        await render(<ModelTableNameCell row={mockedTrainedModel} defaultDescription={description} />);

        expect(screen.getByText(description)).toBeVisible();
        expect(screen.getByText(mockedModel.modelName)).toBeVisible();
    });
});
