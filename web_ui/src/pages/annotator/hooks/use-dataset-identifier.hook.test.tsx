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

import { ReactNode } from 'react';

import { renderHook, waitFor } from '@testing-library/react';

import { ProjectProvider } from '../../../pages/project-details/providers/project-provider/project-provider.component';
import { getMockedProjectIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { RequiredProviders } from '../../../test-utils/required-providers-render';
import { useDatasetIdentifier } from './use-dataset-identifier.hook';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        projectId: 'project-id',
        datasetId: 'some-id',
        organizationId: 'organization-123',
    }),
}));

jest.mock('../../../pages/project-details/providers/project-provider/project-provider.component', () => ({
    ...jest.requireActual('../../../pages/project-details/providers/project-provider/project-provider.component'),
    useProject: jest.fn(),
}));

jest.mock('../../../hooks/use-project-identifier/use-project-identifier', () => {
    return {
        useProjectIdentifier: jest.fn(() => {
            return {
                workspaceId: 'workspace-id',
                projectId: 'project-id',
                organizationId: 'organization-id',
            };
        }),
    };
});

jest.mock('../../project-details/components/project-dataset/use-selected-dataset/use-selected-dataset.hook', () => {
    return {
        useSelectedDataset: jest.fn(() => {
            return {
                id: 'dataset-id',
                name: 'dataset',
                useForTraining: true,
                creationTime: '2022-07-22T20:09:22.576000+00:00',
            };
        }),
    };
});

const wrapper = ({ children }: { children: ReactNode }) => {
    return (
        <RequiredProviders>
            <ProjectProvider
                projectIdentifier={getMockedProjectIdentifier({
                    workspaceId: 'workspace-id',
                    projectId: 'project-id',
                })}
            >
                {children}
            </ProjectProvider>
        </RequiredProviders>
    );
};

describe('useDatasetIdentifier', () => {
    afterAll(() => {
        jest.clearAllMocks();
    });

    it('returns the correct workspaceId, projectId and datasetId', async () => {
        const { result } = renderHook(() => useDatasetIdentifier(), { wrapper });

        await waitFor(() => {
            expect(result.current.projectId).toEqual('project-id');
            expect(result.current.workspaceId).toEqual('workspace-id');
            expect(result.current.datasetId).toEqual('dataset-id');
        });
    });
});
