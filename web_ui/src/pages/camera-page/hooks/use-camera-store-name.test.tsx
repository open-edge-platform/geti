// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { waitFor } from '@testing-library/react';

import { createInMemoryProjectService } from '../../../core/projects/services/in-memory-project-service';
import { getMockedProjectIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedProject } from '../../../test-utils/mocked-items-factory/mocked-project';
import { renderHookWithProviders } from '../../../test-utils/render-hook-with-providers';
import { ProjectProvider } from '../../project-details/providers/project-provider/project-provider.component';
import { useCameraStoreName } from './use-camera-store-name.hook';

jest.mock('localforage');

const wrapper = ({ children, projectId }: { children?: ReactNode; projectId?: string }) => {
    return <ProjectProvider projectIdentifier={getMockedProjectIdentifier({ projectId })}>{children}</ProjectProvider>;
};

const renderCameraStoreNameHook = ({
    projectId,
    datasetId = 'datasetId-test',
    initialEntries = [''],
}: {
    projectId?: string;
    datasetId?: string;
    initialEntries?: string[];
}) => {
    const projectService = createInMemoryProjectService();
    projectService.getProject = async () =>
        getMockedProject({
            datasets: [
                {
                    id: datasetId,
                    name: 'Mocked dataset',
                    useForTraining: true,
                    creationTime: '2022-07-22T20:09:22.576000+00:00',
                },
            ],
        });

    return renderHookWithProviders(() => useCameraStoreName(), {
        wrapper: ({ children }) => wrapper({ children, projectId }),
        providerProps: {
            initialEntries,
            projectService,
        },
    });
};

describe('useCameraStoreName', () => {
    it('livePrediction false, use dataset id as store name', async () => {
        const datasetId = '123';
        const { result } = renderCameraStoreNameHook({ datasetId });

        await waitFor(() => {
            expect(result.current).toBe(`dataset-${datasetId}`);
        });
    });

    it('livePrediction param true', async () => {
        const { result } = renderCameraStoreNameHook({ initialEntries: ['?isLivePrediction=true'] });

        await waitFor(() => {
            expect(result.current).toContain(`project-live-inference-`);
        });
    });

    it('livePrediction page', async () => {
        const { result } = renderCameraStoreNameHook({
            initialEntries: [
                '/organizations/organization-id/workspaces/workspaces-id/projects/projects-id/tests/live-prediction',
            ],
        });

        await waitFor(() => {
            expect(result.current).toContain(`project-live-inference-`);
        });
    });
});
