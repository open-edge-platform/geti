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

import { screen, waitFor } from '@testing-library/react';

import { createInMemoryTestsService } from '../../../../core/tests/services/in-memory-tests-service';
import { getMockedTestImageMediaItem } from '../../../../core/tests/services/tests-utils';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { MediaItemsBucket } from './media-items-bucket.component';
import { MediaItemsBucketTitle, MediaItemsBucketType } from './media-items-bucket.interface';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        projectId: 'project-id',
        workspaceId: 'workspace_1',
        organizationId: 'organization-id',
    }),
}));

describe('MediaItemsBucket', () => {
    it('should display a Below threshold if value is below threshold', () => {
        render(
            <MediaItemsBucket
                selectedLabelId={'null'}
                title={MediaItemsBucketTitle.BELOW_THRESHOLD}
                type={MediaItemsBucketType.BELOW_THRESHOLD}
                mediaFilterOptions={{}}
                setSelectedTestItem={jest.fn()}
                selectedMediaItem={getMockedTestImageMediaItem()}
            />
        );

        expect(screen.getByTestId('bucket-title-id')).toHaveTextContent(MediaItemsBucketTitle.BELOW_THRESHOLD);
        expect(screen.getByTestId('below_threshold-bucket-container-id')).toHaveClass('mediaBucketBelow', {
            exact: false,
        });
    });

    it('should display a Above threshold text if value is above threshold', () => {
        render(
            <MediaItemsBucket
                selectedLabelId={'null'}
                title={MediaItemsBucketTitle.ABOVE_THRESHOLD}
                type={MediaItemsBucketType.ABOVE_THRESHOLD}
                mediaFilterOptions={{}}
                setSelectedTestItem={jest.fn()}
                selectedMediaItem={getMockedTestImageMediaItem()}
            />
        );

        expect(screen.getByTestId('bucket-title-id')).toHaveTextContent(MediaItemsBucketTitle.ABOVE_THRESHOLD);
        expect(screen.getByTestId('above_threshold-bucket-container-id')).toHaveClass('mediaBucketAbove', {
            exact: false,
        });
    });

    it('should correctly display the media count', async () => {
        const testsService = createInMemoryTestsService();

        testsService.getTestMediaAdvancedFilter = jest.fn(async () => {
            return Promise.resolve({
                media: [getMockedTestImageMediaItem(), getMockedTestImageMediaItem(), getMockedTestImageMediaItem()],
                nextPage: undefined,
                totalImages: 10,
                totalVideos: 2,
                totalMatchedImages: 3,
                totalMatchedVideos: 1,
                totalMatchedVideoFrames: 50,
            });
        });

        render(
            <MediaItemsBucket
                selectedLabelId={'null'}
                title={MediaItemsBucketTitle.BELOW_THRESHOLD}
                type={MediaItemsBucketType.BELOW_THRESHOLD}
                mediaFilterOptions={{}}
                setSelectedTestItem={jest.fn()}
                selectedMediaItem={getMockedTestImageMediaItem()}
            />,
            { services: { testsService } }
        );

        await waitFor(() => {
            expect(screen.getByText('3 images, 50 frames from 1 video')).toBeInTheDocument();
        });
    });
});
