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

import { fireEvent, screen } from '@testing-library/react';

import { ModelsGroups } from '../../../../core/models/models.interface';
import { mockedArchitectureModels } from '../../../../core/models/services/test-utils';
import { ApplicationServicesContextProps } from '../../../../core/services/application-services-provider.component';
import { PerformanceCategory } from '../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { useSupportedAlgorithms } from '../../../../core/supported-algorithms/hooks/use-supported-algorithms.hook';
import { getMockedSupportedAlgorithm } from '../../../../core/supported-algorithms/services/test-utils';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { ModelSelection } from './model-selection.component';

jest.mock('../../../../core/supported-algorithms/hooks/use-supported-algorithms.hook', () => ({
    ...jest.requireActual('../../../../core/supported-algorithms/hooks/use-supported-algorithms.hook'),
    useSupportedAlgorithms: jest.fn(),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        projectId: 'project-id',
        organizationId: 'organization-id',
        workspaceId: 'workspace_1',
    }),
}));

const renderApp = async ({
    models,
    services,
}: {
    services?: Partial<ApplicationServicesContextProps>;
    models: ModelsGroups[];
}) => {
    await render(
        <ModelSelection
            models={models}
            selectModel={jest.fn()}
            selectedModel={{
                modelGroupId: '',
                versionId: '',
                optimisationId: undefined,
                modelId: '',
            }}
        />,
        { services }
    );
};

describe('ModelSelection', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('render all model architectures and performance categories', async () => {
        // @ts-expect-error we only care about modelTemplateId and performanceCategory
        jest.mocked(useSupportedAlgorithms).mockReturnValue({
            data: [
                getMockedSupportedAlgorithm({
                    modelTemplateId: 'Custom_Object_Detection_Gen3_SSD',
                    performanceCategory: PerformanceCategory.SPEED,
                }),
                getMockedSupportedAlgorithm({
                    modelTemplateId: 'Custom_Semantic_Segmentation_Lite-HRNet-18-mod2_OCR',
                    performanceCategory: PerformanceCategory.ACCURACY,
                }),
            ],
        });
        await renderApp({
            models: mockedArchitectureModels,
        });

        fireEvent.click(await screen.findByRole('button', { name: /architecture/i }));

        expect(await screen.findByRole('option', { name: `YoloV4 (Speed)` })).toBeVisible();
        expect(await screen.findByRole('option', { name: `ATSS (Accuracy)` })).toBeVisible();
    });

    it('does not render performance category if it is OTHER', async () => {
        // @ts-expect-error we only care about modelTemplateId and performanceCategory
        jest.mocked(useSupportedAlgorithms).mockReturnValue({
            data: [
                getMockedSupportedAlgorithm({
                    modelTemplateId: 'Custom_Object_Detection_Gen3_SSD',
                    performanceCategory: PerformanceCategory.OTHER,
                }),
            ],
        });
        await renderApp({
            models: mockedArchitectureModels,
        });

        fireEvent.click(await screen.findByRole('button', { name: /architecture/i }));

        expect(await screen.findByRole('option', { name: `YoloV4` })).toBeVisible();
    });

    it('render all model versions', async () => {
        const [selectedModel] = mockedArchitectureModels;
        await renderApp({ models: mockedArchitectureModels });

        fireEvent.click(screen.getByRole('button', { name: /select version/i }));

        selectedModel.modelVersions.forEach(({ version }) => {
            expect(screen.getByRole('option', { name: `Version ${version}` })).toBeVisible();
        });
    });

    it('filter deleted model versions', async () => {
        const deletedVersion = {
            ...mockedArchitectureModels[0].modelVersions[0],
            purgeInfo: { isPurged: true, userId: null, purgeTime: null },
        };
        const validVersion = { ...mockedArchitectureModels[0].modelVersions[1] };

        const modelWithDeletedModels = {
            ...mockedArchitectureModels[0],
            modelVersions: [deletedVersion, validVersion],
        };

        await renderApp({ models: [modelWithDeletedModels] });

        fireEvent.click(screen.getByRole('button', { name: /select version/i }));

        modelWithDeletedModels.modelVersions.forEach(({ id, version }) => {
            if (deletedVersion.id === id) {
                expect(screen.queryByRole('option', { name: `Version ${version}` })).not.toBeInTheDocument();
            } else {
                expect(screen.getByRole('option', { name: `Version ${version}` })).toBeVisible();
            }
        });
    });
});
