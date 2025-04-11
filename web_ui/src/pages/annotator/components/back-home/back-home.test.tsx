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

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { paths } from '../../../../core/services/routes';
import { getMockedDataset } from '../../../../test-utils/mocked-items-factory/mocked-datasets';
import { getMockedDatasetIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { CustomRenderOptions, providersRender as render } from '../../../../test-utils/required-providers-render';
import { AnnotatorProviders } from '../../test-utils/annotator-render';
import { BackHome } from './back-home.component';

jest.mock('../../providers/submit-annotations-provider/submit-annotations-provider.component', () => ({
    ...jest.requireActual('../../providers/submit-annotations-provider/submit-annotations-provider.component'),
    useSubmitAnnotations: () => ({ confirmSaveAnnotations: (callback: () => Promise<void>) => callback() }),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: jest.fn(),
    useSearchParams: jest.fn(() => [new URLSearchParams()]),
    useParams: () => ({
        projectId: 'project-id',
        workspaceId: 'workspace_1',
        organizationId: 'organization-id',
    }),
}));

const datasetIdentifier = getMockedDatasetIdentifier({
    workspaceId: 'workspace_1',
    projectId: 'project-id',
    datasetId: 'in-memory-dataset',
});

const renderBackHome = async (options: CustomRenderOptions = {}) => {
    render(
        <AnnotatorProviders datasetIdentifier={datasetIdentifier}>
            <BackHome />
        </AnnotatorProviders>,
        options
    );
    await waitForElementToBeRemoved(screen.getByRole('progressbar'));
};

describe('BackHome component', () => {
    const mockNavigate = jest.fn();

    jest.mocked(useNavigate).mockImplementation(() => mockNavigate);

    afterEach(() => {
        mockNavigate.mockReset();
    });

    const expectedMediaRoute = paths.project.dataset.media(datasetIdentifier);

    it('Goes back to the project page', async () => {
        await renderBackHome();

        fireEvent.click(screen.getByTestId('go-back-button'));

        expect(mockNavigate).toHaveBeenCalledWith(expectedMediaRoute);
    });

    it('Remembers the dataset filter', async () => {
        jest.mocked(useSearchParams).mockImplementation(() => [new URLSearchParams([['filter', 'test']]), jest.fn()]);

        await renderBackHome();

        fireEvent.click(screen.getByTestId('go-back-button'));

        expect(mockNavigate).toHaveBeenCalledWith(`${expectedMediaRoute}?filter=test`);
    });

    it('Sets the dataset filter for both normal and anomalous buckets', async () => {
        jest.mocked(useSearchParams).mockImplementation(() => [new URLSearchParams([['filter', 'test']]), jest.fn()]);
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () => {
            return getMockedProject({
                tasks: [getMockedTask({ domain: DOMAIN.ANOMALY_DETECTION })],
                datasets: [getMockedDataset({ id: 'in-memory-dataset' })],
            });
        };

        await renderBackHome({ services: { projectService } });

        fireEvent.click(screen.getByTestId('go-back-button'));

        expect(mockNavigate).toHaveBeenCalledWith(`${expectedMediaRoute}?filter-normal=test&filter-anomalous=test`);
    });

    describe('sorting params', () => {
        it('empty filter', async () => {
            jest.mocked(useSearchParams).mockImplementation(() => [
                new URLSearchParams([
                    ['sortBy', 'name'],
                    ['sortDirection', 'desc'],
                ]),
                jest.fn(),
            ]);

            await renderBackHome();

            fireEvent.click(screen.getByTestId('go-back-button'));

            expect(mockNavigate).toHaveBeenCalledWith(`${expectedMediaRoute}?sortBy=name&sortDirection=desc`);
        });

        it('filter and sorting', async () => {
            jest.mocked(useSearchParams).mockImplementation(() => [
                new URLSearchParams([
                    ['filter', 'test'],
                    ['sortBy', 'name'],
                    ['sortDirection', 'desc'],
                ]),
                jest.fn(),
            ]);

            await renderBackHome();

            fireEvent.click(screen.getByTestId('go-back-button'));

            expect(mockNavigate).toHaveBeenCalledWith(
                `${expectedMediaRoute}?filter=test&sortBy=name&sortDirection=desc`
            );
        });
    });
});
