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

import { screen, waitForElementToBeRemoved } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { Dataset } from '../../../../core/projects/dataset.interface';
import { PerformanceType } from '../../../../core/projects/task.interface';
import { useModelIdentifier } from '../../../../hooks/use-model-identifier/use-model-identifier.hook';
import { useProjectIdentifier } from '../../../../hooks/use-project-identifier/use-project-identifier';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { useProject } from '../../providers/project-provider/project-provider.component';
import ModelPage from './project-model.component';

jest.mock('../../../../hooks/use-model-identifier/use-model-identifier.hook', () => ({
    useModelIdentifier: jest.fn(),
}));

jest.mock('../../../../hooks/use-project-identifier/use-project-identifier', () => ({
    useProjectIdentifier: jest.fn(),
}));

jest.mock('../../providers/project-provider/project-provider.component', () => ({
    ...jest.requireActual('../../providers/project-provider/project-provider.component'),
    useProject: jest.fn(() => ({
        project: {},
    })),
}));

const mockedProjectIdentifier = {
    organizationId: 'organization-id',
    projectId: 'project-1',
    workspaceId: 'workspace-1',
};

describe('ProjectModel', () => {
    beforeAll(() => {
        jest.mocked(useModelIdentifier).mockImplementation(() => ({
            organizationId: 'organization-id',
            taskName: 'Test task',
            groupId: 'model-group-1-id',
            projectId: 'project-1',
            workspaceId: 'workspace-1',
            modelId: '3',
        }));

        jest.mocked(useProjectIdentifier).mockImplementation(() => mockedProjectIdentifier);

        //@ts-expect-error there is no need to mock all of the project fields
        jest.mocked(useProject).mockImplementation(() => ({
            projectIdentifier: mockedProjectIdentifier,
            isTaskChainProject: false,
            project: getMockedProject({
                tasks: [{ labels: [], id: '1234', title: 'Task 1', domain: DOMAIN.DETECTION }],
                labels: [],
                domains: [DOMAIN.DETECTION],
                id: 'project-1',
                name: 'Project 1',
                datasets: [
                    {
                        id: 'dataset-1',
                        name: 'Default dataset',
                        useForTraining: false,
                        creationTime: new Date(Date.now()).toString(),
                    },
                ] as Dataset[],
                performance: {
                    type: PerformanceType.DEFAULT,
                    score: 0.9,
                    taskPerformances: [{ score: { value: 0.9, metricType: 'accuracy' }, taskNodeId: 'task-id' }],
                },
                creationDate: new Date(Date.now()),
                thumbnail: 'thumbnail',
                storageInfo: {},
            }),
            isSingleDomainProject: jest.fn(),
        }));
    });

    it('Check if there are all tabs and first one (Model variants) is selected', async () => {
        await render(<ModelPage />);

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        expect(screen.getByRole('tab', { name: 'Model variants' })).toHaveAttribute('aria-selected', 'true');
        expect(screen.getByRole('tab', { name: 'Training datasets' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Model metrics' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Parameters' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Labels' })).toBeInTheDocument();
    });

    it("Select 'Training dataset' tab and check if proper component is selected", async () => {
        await render(<ModelPage />);

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        const trainingDatasetTab = screen.getByRole('tab', { name: 'Training datasets' });

        await userEvent.click(trainingDatasetTab);
        expect(trainingDatasetTab).toHaveAttribute('aria-selected', 'true');
    });
});
