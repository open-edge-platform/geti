// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { screen } from '@testing-library/react';

import { mockedOptimizedModels, mockedTrainedModel } from '../../../../../core/models/services/test-utils';
import { projectRender as render } from '../../../../../test-utils/project-provider-render';
import { ModelVariants, ModelVariantsProps } from './model-variants.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        projectId: 'project-123',
        workspaceId: 'workspace-123',
        organizationId: 'organization-123',
    }),
}));
jest.mock('../../../hooks/use-tasks-with-supported-algorithms', () => ({
    ...jest.requireActual('../../../hooks/use-tasks-with-supported-algorithms'),
    useTasksWithSupportedAlgorithms: () => ({
        tasksWithSupportedAlgorithms: {
            '321': [
                {
                    domain: 'Classification',
                    summary: 'Class-Incremental Image Classification for EfficientNet-B0',
                    gigaflops: 0.81,
                    isDefaultAlgorithm: true,
                    modelSize: 4.09,
                    name: 'EfficientNet-B0',
                    modelTemplateId: 'Custom_Image_Classification_EfficinetNet-B0',
                },
            ],
        },
    }),
}));

const modelVariantsProps: ModelVariantsProps = {
    modelDetails: {
        trainedModel: mockedTrainedModel,
        optimizedModels: mockedOptimizedModels,
        trainingDatasetInfo: { revisionId: 'dataset-test-revision-id', storageId: 'dataset-test-storage-id' },
        labels: [],
    },
    refetchModels: jest.fn(),
    areOptimizedModelsVisible: true,
    isPOTModel: false,
    groupName: 'Name',
    modelTemplateName: 'Speed',
    taskId: '321',
    version: 1,
};

// TO DO: IMPLEMENT TESTS ONCE SPECTRUM TABLE IS IMPLEMENTED
describe('Model variants', () => {
    it('renders optimized model', async () => {
        await render(<ModelVariants {...modelVariantsProps} />);

        expect(screen.getByRole('button', { name: /Start optimization/i })).toBeVisible();
    });

    it('"Start optimization" is hidden if model has been deleted', async () => {
        await render(
            <ModelVariants
                {...modelVariantsProps}
                modelDetails={{
                    ...modelVariantsProps.modelDetails,
                    purgeInfo: { isPurged: true, purgeTime: 'purgeTime', userId: 'userId' },
                }}
            />
        );

        expect(screen.queryByRole('button', { name: /Start optimization/i })).not.toBeInTheDocument();
    });
});
