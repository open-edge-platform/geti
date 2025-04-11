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

import { screen } from '@testing-library/react';
import dayjs from 'dayjs';

import { MEDIA_ANNOTATION_STATUS } from '../../../../../core/media/base.interface';
import { MediaItem } from '../../../../../core/media/media.interface';
import { getFileSize } from '../../../../../shared/utils';
import { getMockedImageMediaItem } from '../../../../../test-utils/mocked-items-factory/mocked-media';
import { getMockedUser } from '../../../../../test-utils/mocked-items-factory/mocked-users';
import { getMediaId } from '../../../../media/utils';
import { annotatorRender as render } from '../../../test-utils/annotator-render';
import { DatasetItemMenu } from './dataset-item-menu.component';
import { DatasetListItemDetails } from './dataset-list-item-details.component';
import { formatUploadTime } from './utils';

const MOCKED_USER = getMockedUser();

jest.mock('../../../../../core/users/hook/use-users.hook', () => ({
    useUsers: jest.fn(() => ({
        useGetUserQuery: () => ({
            data: MOCKED_USER,
        }),
        useActiveUser: jest.fn(() => ({ data: MOCKED_USER })),
    })),
}));

describe('DatasetListItemDetails', () => {
    const mockedMediaItem = getMockedImageMediaItem({
        name: 'Test media item',
        uploadTime: dayjs().toString(),
        metadata: { size: 1234, width: 1000, height: 1000 },
        annotationStatePerTask: [{ taskId: 'task-id', state: MEDIA_ANNOTATION_STATUS.ANNOTATED }],
        lastAnnotatorId: 'user-1-id',
    });

    const mediaId = getMediaId(mockedMediaItem);

    const renderDetails = async (mediaItem: MediaItem, isSelected: boolean, shouldShowAnnotationIndicator: boolean) => {
        await render(
            <DatasetListItemDetails
                mediaItem={mediaItem}
                isSelected={isSelected}
                selectMediaItem={jest.fn()}
                shouldShowAnnotationIndicator={shouldShowAnnotationIndicator}
                datasetItemMenu={<DatasetItemMenu mediaItem={mediaItem} isSelected={isSelected} />}
            />
        );
    };

    it('Should show details about media item', async () => {
        await renderDetails(mockedMediaItem, false, false);

        const {
            name,
            uploadTime,
            metadata: { size },
        } = mockedMediaItem;

        expect(screen.getByTestId('image-placeholder-id')).toBeInTheDocument();
        expect(screen.getByText(name)).toBeInTheDocument();
        expect(screen.getByText(`${formatUploadTime(uploadTime)} | ${getFileSize(size)}`)).toBeInTheDocument();
        expect(screen.getByText(MOCKED_USER.firstName as string)).toBeInTheDocument();
    });

    it('Details row should has border indicator when is selected', async () => {
        await renderDetails(mockedMediaItem, true, false);

        expect(screen.getByTestId(mediaId)).toHaveClass('itemDetailsSelected', {
            exact: false,
        });
    });

    it('Details row should NOT has border indicator when is NOT selected', async () => {
        await renderDetails(mockedMediaItem, false, false);

        expect(screen.getByTestId(mediaId)).not.toHaveClass('itemDetailsSelected', {
            exact: false,
        });
    });

    it('Details row should has delete menu', async () => {
        await renderDetails(mockedMediaItem, false, false);

        expect(screen.getByRole('button', { name: /open menu/i })).toBeInTheDocument();
    });

    it('Details should display annotation indicator', async () => {
        await renderDetails(mockedMediaItem, false, true);

        expect(screen.getByRole('button', { name: /annotated/i })).toBeInTheDocument();
    });

    it('Details should not display annotation indicator', async () => {
        await renderDetails(mockedMediaItem, false, false);

        expect(screen.queryByRole('button', { name: /annotated/i })).not.toBeInTheDocument();
    });
});
