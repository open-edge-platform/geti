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

import { fireEvent, screen } from '@testing-library/react';
import { useNavigate } from 'react-router-dom';

import { MediaItem } from '../../../../core/media/media.interface';
import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { EditAnnotationsButton } from './edit-annotations-button.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: jest.fn(),
}));

describe('EditAnnotationsButton Component', () => {
    it('Check if button properly navigates to annotator', async () => {
        const useNavigateMock = jest.fn();

        jest.mocked(useNavigate).mockImplementation(() => useNavigateMock);

        const datasetIdentifier: DatasetIdentifier = {
            projectId: 'test-project',
            datasetId: 'test-dataset',
            workspaceId: 'test-workspace',
            organizationId: 'organization-id',
        };

        const mediaItem: MediaItem = getMockedImageMediaItem({
            name: 'item-image',
        });

        render(<EditAnnotationsButton datasetIdentifier={datasetIdentifier} mediaItem={mediaItem} />);
        fireEvent.click(screen.getByRole('button', { name: 'Edit annotations' }));

        expect(useNavigateMock).toHaveBeenCalledWith(
            '/organizations/organization-id/workspaces/test-workspace/projects/test-project/datasets/test-dataset/annotator/image/test-image'
        );
    });
});
