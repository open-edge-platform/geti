// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ViewModes } from '@shared/components/media-view-modes/utils';
import { InfiniteData, UseInfiniteQueryResult } from '@tanstack/react-query';
import { screen, waitFor } from '@testing-library/react';

import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { TestMediaAdvancedFilter } from '../../../../core/tests/test-media.interface';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { checkTooltip } from '../../../../test-utils/utils';
import { TestMediaItemsList } from './test-media-items-list.component';

describe('TestMediaItemsList component', () => {
    it('Check media item', async () => {
        const mediaItemsQuery = {
            isFetching: false,
            isPending: false,
            data: {
                pages: [
                    {
                        media: [
                            {
                                type: MEDIA_TYPE.IMAGE,
                                media: getMockedImageMediaItem({ name: 'test image' }),
                                testResult: {
                                    annotationId: 'annotation id',
                                    predictionId: 'prediction id',
                                    scores: [{ name: 'test', labelId: 'label id', value: 0.6 }],
                                },
                            },
                        ],
                    },
                ],
            },
        } as UseInfiniteQueryResult<InfiniteData<TestMediaAdvancedFilter>>;
        const mockLoadNextMedia = jest.fn();

        await render(
            <TestMediaItemsList
                viewMode={ViewModes.MEDIUM}
                loadNextMedia={mockLoadNextMedia}
                mediaItemsQuery={mediaItemsQuery}
                selectMediaItem={jest.fn()}
                shouldShowAnnotationIndicator={false}
                selectedMediaItem={getMockedImageMediaItem({ name: 'test' })}
            />
        );

        await checkTooltip(screen.getByTestId('test image(100x100)'), 'File name: test image');

        expect(screen.getByText('Size: 696.97 KB')).toBeVisible();
        expect(screen.getByText('Resolution: 100x100')).toBeVisible();
        expect(screen.getByText('Upload time: 22 Jun 2022 00:00:00')).toBeVisible();
        expect(screen.getByTestId('test image(100x100)')).toBeInTheDocument();

        await waitFor(() => {
            expect(screen.getByText('Owner: Test User')).toBeVisible();
        });
    });
});
