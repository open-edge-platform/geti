// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';
import dayjs from 'dayjs';

import { createInMemoryModelsService } from '../../../../../../core/models/services/in-memory-models-service';
import { ModelsService } from '../../../../../../core/models/services/models.interface';
import { formatDate } from '../../../../../../shared/utils';
import { getMockedProjectIdentifier } from '../../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedModelVersion } from '../../../../../../test-utils/mocked-items-factory/mocked-model';
import { providersRender } from '../../../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../../providers/project-provider/project-provider.component';
import { ModelCard } from './model-card.component';
import { ModelVersion } from './model-card.interface';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: jest.fn(),
    useParams: () => ({
        projectId: 'project-id',
        workspaceId: 'workspace-id',
        organizationId: 'organization-id',
    }),
}));

describe('Model card', () => {
    afterAll(() => {
        jest.clearAllTimers();
    });

    beforeEach(() => {
        jest.clearAllMocks();
    });

    const creationDate = dayjs().toString();
    const modelActive = getMockedModelVersion({ isActiveModel: true });
    const modelInactive = getMockedModelVersion({ isActiveModel: false });
    const modelDeleted = getMockedModelVersion({ purgeInfo: { isPurged: true, userId: null, purgeTime: null } });

    const activeModelLabel = 'Active model';
    const labelsOutOfDate = 'Labels out-of-date';

    const activateModel = jest.fn(() => Promise.resolve());
    const trainModel = jest.fn(() => Promise.resolve());

    const defaultModelsService = createInMemoryModelsService();
    defaultModelsService.activateModel = activateModel;
    defaultModelsService.trainModel = trainModel;

    const render = async ({
        model = modelActive,
        isLatestModel = true,
        modelsService = defaultModelsService,
        isMenuOptionsDisabled = false,
        complexity = undefined,
    }: {
        model?: ModelVersion;
        isLatestModel?: boolean;
        modelsService?: ModelsService;
        isMenuOptionsDisabled?: boolean;
        complexity?: number;
    } = {}) => {
        providersRender(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
                <ModelCard
                    model={model}
                    isLatestModel={isLatestModel}
                    taskId={'1'}
                    modelTemplateId={'template-id'}
                    isMenuOptionsDisabled={isMenuOptionsDisabled}
                    complexity={complexity}
                />
            </ProjectProvider>,
            {
                services: {
                    modelsService,
                },
            }
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    it('should display generic information about model: version, creation time, complexity, size', async () => {
        const { groupId, id: modelId, version } = modelActive;
        const id = `${groupId}-${modelId}`;

        await render({ complexity: 1 });

        expect(screen.getByTestId(`version-${id}-id`)).toHaveTextContent(`Version ${version}`);

        const formattedCreationDate = formatDate(creationDate, 'DD MMM YYYY, hh:mm A');

        expect(screen.getByTestId('trained-model-date-id')).toHaveTextContent(`Trained: ${formattedCreationDate}`);

        await waitFor(() => {
            const container = screen.getByTestId('model-info-architecture-id-model-id-id');

            expect(container).toHaveTextContent('Model weight size: 23.20 MB');
            expect(container).toHaveTextContent('Total size: 10 MB');
            expect(container).toHaveTextContent('Complexity: 1 GFlops');
        });
    });

    it('does not show complexity when this is not available', async () => {
        const { groupId, id: modelId, version } = modelActive;
        const id = `${groupId}-${modelId}`;

        await render();

        expect(screen.getByTestId(`version-${id}-id`)).toHaveTextContent(`Version ${version}`);

        const formattedCreationDate = formatDate(creationDate, 'DD MMM YYYY, hh:mm A');

        expect(screen.getByTestId('trained-model-date-id')).toHaveTextContent(`Trained: ${formattedCreationDate}`);

        const container = screen.getByTestId('model-info-architecture-id-model-id-id');
        await waitFor(() => {
            expect(container).toHaveTextContent('Model weight size: 23.20 MB');
            expect(container).toHaveTextContent('Total size: 10 MB');
        });

        expect(container).not.toHaveTextContent('Complexity');
    });

    it('should not display weight and size if the modal is deleted', async () => {
        const { groupId, id: modelId, version } = modelDeleted;
        const id = `${groupId}-${modelId}`;

        await render({ model: modelDeleted });

        expect(screen.getByTestId(`version-${id}-id`)).toHaveTextContent(`Version ${version}`);

        await waitFor(() => {
            const container = screen.getByTestId('model-info-architecture-id-model-id-id');

            expect(container).not.toHaveTextContent('Model weight size: 23.20 MB');
            expect(container).not.toHaveTextContent('Total size: 10 MB');
            expect(container).not.toHaveTextContent('GFlops');
        });
    });

    it('should display count of labels, images and frames', async () => {
        const { groupId, id: modelId } = modelActive;
        const id = `${groupId}-${modelId}`;

        const { labels, trainedModel } = await defaultModelsService.getModel({
            ...getMockedProjectIdentifier(),
            groupId,
            modelId,
        });

        const numberOfLabels = labels.length;
        const numberOfImages = trainedModel.numberOfImages;
        const numberOfFrames = trainedModel.numberOfFrames;

        await render();

        await waitFor(() => {
            expect(screen.getByTestId(`label-count-${id}-id`)).toHaveTextContent(
                numberOfLabels === 1 ? `${numberOfLabels} label` : `${numberOfLabels} labels`
            );
        });
        expect(screen.getByTestId(`image-count-${id}-id`)).toHaveTextContent(
            numberOfImages === 1 ? `${numberOfImages} image` : `${numberOfImages} images`
        );
        expect(screen.getByTestId(`frame-count-${id}-id`)).toHaveTextContent(
            numberOfFrames === 1 ? `${numberOfFrames} frame` : `${numberOfFrames} frames`
        );
    });

    it('should display active tag when model is active', async () => {
        await render();

        expect(screen.getByText(activeModelLabel)).toBeInTheDocument();
    });

    it('should not display active tag when model is inactive', async () => {
        await render({ model: modelInactive });

        expect(screen.queryByText(activeModelLabel)).not.toBeInTheDocument();
    });

    it("should not display labels out of date tag when labels' schema is up to date", async () => {
        await render({ model: getMockedModelVersion({ isLabelSchemaUpToDate: true }) });

        expect(screen.queryByText(labelsOutOfDate)).not.toBeInTheDocument();
    });

    describe("Labels' schema", () => {
        const modelInactiveAndLabelsOutdated = getMockedModelVersion({
            isActiveModel: false,
            isLabelSchemaUpToDate: false,
        });

        it("should display labels out of date tag when labels' schema has changed", async () => {
            await render({ model: modelInactiveAndLabelsOutdated });

            expect(screen.getByText(labelsOutOfDate)).toBeInTheDocument();
        });
    });
});
