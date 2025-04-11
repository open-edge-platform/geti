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

import { act, waitFor } from '@testing-library/react';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { getMockedProjectIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { renderHookWithProviders } from '../../../test-utils/render-hook-with-providers';
import { createInMemoryProjectService } from '../services/in-memory-project-service';
import { ProjectService } from '../services/project-service.interface';
import { useProjectActions } from './use-project-actions.hook';

const mockAddNotification = jest.fn();
jest.mock('../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../notification/notification.component'),
    useNotification: () => ({ addNotification: mockAddNotification }),
}));

const renderProjectActionsHook = ({ projectService }: { projectService: ProjectService }) => {
    return renderHookWithProviders(() => useProjectActions(), {
        providerProps: {
            projectService,
        },
    });
};

describe('useProjectActions', () => {
    describe('deleteProjectMutation', () => {
        it('call setQueryData when resolve successfully', async () => {
            const projectService = createInMemoryProjectService();
            projectService.deleteProject = jest.fn(async () => '');

            const { result } = renderProjectActionsHook({ projectService });

            const mockData = getMockedProjectIdentifier({ workspaceId: '1', projectId: '4' });

            act(() => {
                result.current.deleteProjectMutation.mutate(mockData);
            });

            await waitFor(() => {
                expect(projectService.deleteProject).toHaveBeenCalledWith(mockData);
            });

            expect(mockAddNotification).not.toHaveBeenCalled();
        });

        it('call addNotification when rejects', async () => {
            const error = { message: 'test' };
            const projectService = createInMemoryProjectService();
            projectService.deleteProject = jest.fn(() => Promise.reject(error));

            const { result } = renderProjectActionsHook({ projectService });

            const mockData = getMockedProjectIdentifier({ workspaceId: '1', projectId: '4' });

            act(() => {
                result.current.deleteProjectMutation.mutate(mockData);
            });

            await waitFor(() => {
                expect(projectService.deleteProject).toHaveBeenCalledWith(mockData);
            });

            expect(mockAddNotification).toHaveBeenCalledWith({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
        });
    });
});
