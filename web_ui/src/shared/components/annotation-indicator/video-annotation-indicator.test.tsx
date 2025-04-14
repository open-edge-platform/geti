// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { MEDIA_ANNOTATION_STATUS } from '../../../core/media/base.interface';
import { MediaItem } from '../../../core/media/media.interface';
import { Video } from '../../../core/media/video.interface';
import {
    getMockedImageMediaItem,
    getMockedVideoMediaItem,
} from '../../../test-utils/mocked-items-factory/mocked-media';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { onHoverTooltip } from '../../../test-utils/utils';
import { VideoAnnotationIndicator } from './video-annotation-indicator.component';

const openTooltip = () => {
    const indicator = screen.getByRole('button', { name: 'annotation state indicator' });
    expect(indicator).toBeVisible();

    jest.useFakeTimers();
    onHoverTooltip(indicator);
    jest.advanceTimersByTime(750);
};

describe('VideoAnnotationIndicator', () => {
    const imageMediaItem = getMockedImageMediaItem({
        annotationStatePerTask: [{ taskId: 'task-id', state: MEDIA_ANNOTATION_STATUS.ANNOTATED }],
    });

    const renderMedia = (mediaItem: MediaItem = imageMediaItem) => {
        return render(<VideoAnnotationIndicator video={mediaItem as Video} />);
    };

    afterAll(() => {
        jest.useRealTimers();
        jest.clearAllTimers();
    });

    it('does not render with invalid statistics', async () => {
        const videoMediaItem = getMockedVideoMediaItem({ annotationStatistics: undefined });

        renderMedia(videoMediaItem);

        expect(screen.queryByRole('button', { name: 'annotation state indicator' })).not.toBeInTheDocument();
    });

    it('contains annotated frame', async () => {
        const annotationStatistics = { annotated: 1, partiallyAnnotated: 0, unannotated: 0 };
        const videoMediaItem = getMockedVideoMediaItem({ annotationStatistics });

        renderMedia(videoMediaItem);
        openTooltip();

        expect(
            await screen.findByText(new RegExp(`${annotationStatistics.annotated} frame annotated`))
        ).toBeInTheDocument();

        expect(screen.getByTestId('annotation-state-indicator-id')).toHaveClass('annotated');
    });

    it('contains partially annotated frame', async () => {
        const annotationStatistics = { annotated: 0, partiallyAnnotated: 1, unannotated: 0 };
        const videoMediaItem = getMockedVideoMediaItem({ annotationStatistics });

        renderMedia(videoMediaItem);
        openTooltip();

        expect(
            await screen.findByText(new RegExp(`${annotationStatistics.partiallyAnnotated} frame partially annotated`))
        ).toBeInTheDocument();

        expect(screen.getByTestId('annotation-state-indicator-id')).toHaveClass('partially_annotated');
    });

    it('contains annotated and partially annotated frame', async () => {
        const annotationStatistics = { annotated: 1, partiallyAnnotated: 1, unannotated: 0 };
        const videoMediaItem = getMockedVideoMediaItem({ annotationStatistics });

        renderMedia(videoMediaItem);
        openTooltip();

        expect(
            await screen.findByText(new RegExp(`${annotationStatistics.annotated} frame annotated`))
        ).toBeInTheDocument();
        expect(
            await screen.findByText(new RegExp(`${annotationStatistics.partiallyAnnotated} frame partially annotated`))
        ).toBeInTheDocument();

        expect(screen.getByTestId('annotation-state-indicator-id')).toHaveClass('both');
    });

    it('contains annotated and partially annotated frames (pluralize)', async () => {
        const annotationStatistics = { annotated: 3, partiallyAnnotated: 5, unannotated: 0 };
        const videoMediaItem = getMockedVideoMediaItem({ annotationStatistics });

        renderMedia(videoMediaItem);
        openTooltip();

        expect(
            await screen.findByText(new RegExp(`${annotationStatistics.annotated} frames annotated`))
        ).toBeInTheDocument();

        expect(
            await screen.findByText(new RegExp(`${annotationStatistics.partiallyAnnotated} frames partially annotated`))
        ).toBeInTheDocument();

        expect(screen.getByTestId('annotation-state-indicator-id')).toHaveClass('both');
    });
});
