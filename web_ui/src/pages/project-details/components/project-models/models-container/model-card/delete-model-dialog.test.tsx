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

import { fireEvent, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';
import { OverlayTriggerState } from 'react-stately';

import { createInMemoryModelsService } from '../../../../../../core/models/services/in-memory-models-service';
import { ModelsService } from '../../../../../../core/models/services/models.interface';
import { getMockedProjectIdentifier } from '../../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { providersRender } from '../../../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../../providers/project-provider/project-provider.component';
import { DeleteModelDialog } from './delete-model-dialog.component';

const mockDeletionDialogTrigger = {
    isOpen: true,
    open: jest.fn(),
    toggle: jest.fn(),
    setOpen: jest.fn(),
    close: jest.fn(),
};

describe('DeleteModelDialog', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    const mockedModelsService = createInMemoryModelsService();
    mockedModelsService.archiveModel = jest.fn(() => Promise.resolve());

    const render = async ({
        groupId,
        modelId,
        modelsService,
        state = mockDeletionDialogTrigger,
    }: {
        groupId: string;
        modelId: string;
        state?: OverlayTriggerState;
        modelsService: ModelsService;
    }) => {
        providersRender(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
                <DeleteModelDialog
                    overlayState={state}
                    version={1}
                    groupId={groupId}
                    modelId={modelId}
                    modelName={'test-model'}
                />
            </ProjectProvider>,
            { services: { modelsService } }
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    it('calls the service and close the modal', async () => {
        const mockedData = { groupId: '123', modelId: '321' };
        await render({ modelsService: mockedModelsService, ...mockedData });

        fireEvent.click(screen.getByRole('button', { name: /delete model/i }));

        await waitFor(() => {
            expect(mockedModelsService.archiveModel).toHaveBeenCalledWith(expect.objectContaining(mockedData));
        });

        expect(mockDeletionDialogTrigger.close).toHaveBeenCalled();
    });

    it('closes the modal', async () => {
        const mockedData = { groupId: '123', modelId: '321' };
        await render({ modelsService: mockedModelsService, ...mockedData });

        fireEvent.click(screen.getByRole('button', { name: /close delete dialog/i }));

        expect(mockDeletionDialogTrigger.close).toHaveBeenCalled();
    });
});
