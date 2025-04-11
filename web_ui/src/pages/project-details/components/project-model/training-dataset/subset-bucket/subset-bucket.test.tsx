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

import { createInMemoryTrainingDatasetService } from '../../../../../../core/datasets/services/in-memory-training-dataset-service';
import { getMockedProjectIdentifier } from '../../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedImageMediaItem } from '../../../../../../test-utils/mocked-items-factory/mocked-media';
import { projectRender as render } from '../../../../../../test-utils/project-provider-render';
import { getSubsetMediaFilter, Subset } from '../utils';
import { SubsetBucket } from './subset-bucket.component';

jest.mock('uuid', () => ({
    ...jest.requireActual('uuid'),
    v4: jest.fn(() => ''),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
    }),
}));

describe('SubSetBucket component', () => {
    const trainingDatasetService = createInMemoryTrainingDatasetService();
    const projectIdentifier = getMockedProjectIdentifier({
        workspaceId: 'workspace-test',
        projectId: 'project-test',
    });

    const revisionId = 'revision-test';
    const storageId = 'storage-test';
    const taskId = 'task-test';

    it('Check if title is displayed properly and if there is search, filter and sort option visible', async () => {
        trainingDatasetService.getTrainingDatasetMediaAdvancedFilter = jest.fn(async () => ({
            media: [],
            nextPage: undefined,
            totalImages: 3,
            totalVideos: 2,
            totalMatchedImages: 1,
            totalMatchedVideos: 1,
            totalMatchedVideoFrames: 1,
        }));

        await render(
            <SubsetBucket
                mediaPercentage={'20%'}
                projectIdentifier={projectIdentifier}
                type={Subset.TESTING}
                revisionId={revisionId}
                storageId={storageId}
                modelInformation={''}
                modelLabels={[]}
                taskId={taskId}
                isActive={false}
            />,
            { services: { trainingDatasetService } }
        );

        expect(screen.getByTestId('testing-subset-title')).toHaveTextContent('bulb.svgTesting20%');
        expect(screen.getByRole('button', { name: 'Search media by name (regex allowed)' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Filter media' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Sort media' })).toBeInTheDocument();

        const filter = getSubsetMediaFilter(Subset.TESTING);

        expect(trainingDatasetService.getTrainingDatasetMediaAdvancedFilter).toHaveBeenCalledWith(
            projectIdentifier,
            storageId,
            revisionId,
            50,
            null,
            filter,
            {}
        );
    });

    it('Check if preview title is displayed properly', async () => {
        trainingDatasetService.getTrainingDatasetMediaAdvancedFilter = jest.fn(async () => ({
            media: [getMockedImageMediaItem({ name: 'test' })],
            nextPage: undefined,
            totalImages: 3,
            totalVideos: 2,
            totalMatchedImages: 1,
            totalMatchedVideos: 1,
            totalMatchedVideoFrames: 1,
        }));

        await render(
            <SubsetBucket
                mediaPercentage={'20%'}
                projectIdentifier={projectIdentifier}
                type={Subset.TESTING}
                revisionId={revisionId}
                storageId={storageId}
                modelInformation={''}
                modelLabels={[]}
                taskId={taskId}
                isActive={false}
            />,
            { services: { trainingDatasetService } }
        );

        fireEvent.click(await screen.findByTestId('image-test-image'));
        expect(await screen.findByText('Testing subset')).toBeInTheDocument();
    });
});
