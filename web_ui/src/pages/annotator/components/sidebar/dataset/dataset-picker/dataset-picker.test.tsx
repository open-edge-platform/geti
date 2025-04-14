// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { useNavigate } from 'react-router-dom';

import { DOMAIN } from '../../../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../../../core/projects/services/in-memory-project-service';
import { getMockedDatasetIdentifier } from '../../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedProject } from '../../../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { useDataset } from '../../../../providers/dataset-provider/dataset-provider.component';
import { annotatorRender } from '../../../../test-utils/annotator-render';
import { DatasetPicker } from './dataset-picker.component';

jest.mock('../../../../providers/dataset-provider/dataset-provider.component', () => ({
    ...jest.requireActual('../../../../providers/dataset-provider/dataset-provider.component'),
    useDataset: jest.fn(() => ({
        datasetIdentifier: 'some-id',
    })),
}));

const datasetIdentifier = getMockedDatasetIdentifier({});

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: jest.fn(),
}));

describe('DatasetPicker', () => {
    const mockUseDataset = (isInActiveMode = true) => {
        // @ts-expect-error We're only interested in mocking properties used by DatasetPicker
        jest.mocked(useDataset).mockImplementation(() => ({
            isInActiveMode,
            mediaItemsQuery: () => ({
                isFetching: false,
                data: undefined,
            }),
        }));
    };

    it('allows to select the dataset', async () => {
        const mockPush = jest.fn();
        jest.mocked(useNavigate).mockImplementation(() => mockPush);
        mockUseDataset(true);

        await annotatorRender(<DatasetPicker />, { datasetIdentifier });

        expect(screen.queryByRole('option', { hidden: true, name: 'Active set', selected: true })).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Choose annotation dataset/ }));

        await userEvent.selectOptions(
            screen.getByRole('listbox'),
            screen.getByRole('option', { name: 'In memory dataset' })
        );

        expect(mockPush).toHaveBeenCalledWith(
            '/organizations/organization-id/workspaces/workspace-id/projects/project-id/datasets/in-memory-dataset/annotator'
        );
    });

    it('allows to select the active set', async () => {
        const mockPush = jest.fn();
        jest.mocked(useNavigate).mockImplementation(() => mockPush);
        mockUseDataset(false);

        await annotatorRender(<DatasetPicker />, { datasetIdentifier });

        fireEvent.click(screen.getByRole('button', { name: /Choose annotation dataset/ }));

        await userEvent.selectOptions(screen.getByRole('listbox'), screen.getByRole('option', { name: 'Active set' }));

        expect(mockPush).toHaveBeenCalledWith(
            '/organizations/organization-id/workspaces/workspace-id/projects/project-id/datasets/in-memory-dataset/annotator?active=true'
        );
    });

    it('remembers the selected task', async () => {
        const mockPush = jest.fn();
        jest.mocked(useNavigate).mockImplementation(() => mockPush);
        mockUseDataset(false);

        await annotatorRender(<DatasetPicker />, {
            datasetIdentifier,
            initialEntries: [
                '/organizations/organization-id/workspaces/workspace-id/projects/project-id/datasets/in-memory-dataset/annotator?task_id=task',
            ],
        });

        fireEvent.click(screen.getByRole('button', { name: /Choose annotation dataset/ }));

        await userEvent.selectOptions(screen.getByRole('listbox'), screen.getByRole('option', { name: 'Active set' }));

        expect(mockPush).toHaveBeenCalledWith(
            '/organizations/organization-id/workspaces/workspace-id/projects/project-id/datasets/in-memory-dataset/annotator?task_id=task&active=true'
        );
    });

    it('does not show active set for anomaly projects', async () => {
        const anomalyProject = getMockedProject({
            id: datasetIdentifier.projectId,
            tasks: [getMockedTask({ domain: DOMAIN.ANOMALY_CLASSIFICATION })],
        });
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () => anomalyProject;

        const mockPush = jest.fn();
        jest.mocked(useNavigate).mockImplementation(() => mockPush);
        mockUseDataset(false);

        await annotatorRender(<DatasetPicker />, {
            datasetIdentifier,
            services: { projectService },
        });

        anomalyProject.datasets.forEach(({ name }) => {
            expect(screen.getByRole('option', { hidden: true, name })).toBeInTheDocument();
        });
        expect(screen.queryByRole('option', { hidden: true, name: 'Active set' })).not.toBeInTheDocument();
    });
});
