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

import { createInMemoryAnnotationService } from '../../../../core/annotations/services/in-memory-annotation-service';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import {
    getMockedImageMediaItem,
    getMockedVideoFrameMediaItem,
} from '../../../../test-utils/mocked-items-factory/mocked-media';
import { getMockedImage } from '../../../../test-utils/utils';
import {
    useStreamingVideoPlayer,
    VideoPlayerPlayerContextProps,
} from '../../components/video-player/streaming-video-player/streaming-video-player-provider.component';
import {
    SelectedMediaItemProps,
    useSelectedMediaItem,
} from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { SelectedMediaItem } from '../../providers/selected-media-item-provider/selected-media-item.interface';
import { annotatorRender } from '../../test-utils/annotator-render';
import { LayersFactory } from './layers-factory.component';

jest.mock('../../providers/selected-media-item-provider/selected-media-item-provider.component', () => ({
    ...jest.requireActual('../../providers/selected-media-item-provider/selected-media-item-provider.component'),
    useSelectedMediaItem: jest.fn(),
}));

jest.mock('../../components/video-player/streaming-video-player/streaming-video-player-provider.component', () => ({
    ...jest.requireActual(
        '../../components/video-player/streaming-video-player/streaming-video-player-provider.component'
    ),
    useStreamingVideoPlayer: jest.fn(),
}));

const annotationService = createInMemoryAnnotationService();
annotationService.getVideoAnnotations = jest.fn();

const mockContext = fakeAnnotationToolContext({});
const mediaItem = { ...getMockedImageMediaItem({}), image: getMockedImage(), annotations: [] };
const videoItem = { ...getMockedVideoFrameMediaItem({}), image: getMockedImage(), annotations: [] };

const mockAnnotations = [
    getMockedAnnotation({ id: 'test-annotation-1' }),
    getMockedAnnotation({ id: 'test-annotation-2' }),
];

describe('LayersFactory', () => {
    const renderApp = async (selectedMediaItem: SelectedMediaItem = mediaItem, isPlaying = false) => {
        jest.mocked(useStreamingVideoPlayer).mockReturnValue({
            isPlaying,
            currentIndex: 0,
            playbackRate: 10,
            neighbourSize: 10,
            adjustedNeighbourSize: 10,
        } as unknown as VideoPlayerPlayerContextProps);

        jest.mocked(useSelectedMediaItem).mockReturnValue({
            selectedMediaItem,
            selectedMediaItemQuery: { isLoading: false },
            predictionsQuery: { data: undefined },
        } as SelectedMediaItemProps);

        const response = await annotatorRender(
            <LayersFactory
                width={100}
                height={100}
                annotations={mockAnnotations}
                annotationToolContext={mockContext}
            />,
            { services: { annotationService } }
        );

        return response;
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders layers component', async () => {
        await renderApp();

        expect(annotationService.getVideoAnnotations).not.toHaveBeenCalled();
    });

    it('renders video-layers component', async () => {
        await renderApp(videoItem, true);

        expect(annotationService.getVideoAnnotations).toBeCalled();
    });
});
