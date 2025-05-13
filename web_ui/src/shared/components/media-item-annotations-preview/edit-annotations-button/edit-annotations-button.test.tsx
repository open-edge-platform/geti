// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';
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

        expect(screen.getByRole('button', { name: 'Edit annotations' })).toHaveAttribute(
            'href',
            '/organizations/organization-id/workspaces/test-workspace/projects/test-project/datasets/test-dataset/annotator/image/test-image'
        );
    });
});
