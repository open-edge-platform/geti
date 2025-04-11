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

import { createInMemoryInferenceService } from '../../../../core/annotations/services/in-memory-inference-service';
import { InferenceService } from '../../../../core/annotations/services/inference-service.interface';
import { ProjectIdentifier } from '../../../../core/projects/core.interface';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { renderHookWithProviders } from '../../../../test-utils/render-hook-with-providers';
import { TaskContextProps, useTask } from '../task-provider/task-provider.component';
import { useInferenceServerStatus } from './use-inference-server-status';

const mockedAddNotification = jest.fn();
jest.mock('../../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../../notification/notification.component'),
    useNotification: () => ({ addNotification: mockedAddNotification }),
}));

jest.mock('../task-provider/task-provider.component', () => ({
    ...jest.requireActual('../task-provider/task-provider.component'),
    useTask: jest.fn(),
}));

const inferenceService = createInMemoryInferenceService();

inferenceService.getInferenceServerStatus = jest.fn();

const renderInferenceServerStatusHook = (params: {
    projectIdentifier: ProjectIdentifier;
    inferenceService: InferenceService;
}) => {
    return renderHookWithProviders(() => useInferenceServerStatus(params.projectIdentifier), {
        providerProps: { inferenceService: params.inferenceService },
    });
};

describe('useInferenceServerStatus', () => {
    const mockedTaskOne = getMockedTask({ id: '123' });
    const mockedTaskTwo = getMockedTask({ id: '321' });
    const projectIdentifier = getMockedProjectIdentifier();

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('task chain all-task', () => {
        jest.mocked(useTask).mockReturnValue({
            selectedTask: null,
            tasks: [mockedTaskOne, mockedTaskTwo],
        } as TaskContextProps);

        renderInferenceServerStatusHook({ projectIdentifier, inferenceService });

        expect(inferenceService.getInferenceServerStatus).toHaveBeenCalledWith(projectIdentifier, undefined);
    });

    it('task chain selected task', () => {
        jest.mocked(useTask).mockReturnValue({
            selectedTask: mockedTaskOne,
            tasks: [mockedTaskOne, mockedTaskTwo],
        } as TaskContextProps);

        renderInferenceServerStatusHook({ projectIdentifier, inferenceService });

        expect(inferenceService.getInferenceServerStatus).toHaveBeenCalledWith(projectIdentifier, mockedTaskOne.id);
    });

    it('single project', () => {
        jest.mocked(useTask).mockReturnValue({
            tasks: [mockedTaskOne],
            selectedTask: mockedTaskOne,
        } as TaskContextProps);

        renderInferenceServerStatusHook({ projectIdentifier, inferenceService });

        expect(inferenceService.getInferenceServerStatus).toHaveBeenCalledWith(projectIdentifier, undefined);
    });
});
