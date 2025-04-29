// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedVideoFrameMediaItem } from '../../../../../test-utils/mocked-items-factory/mocked-media';
import { annotatorRender as render } from '../../../test-utils/annotator-render';
import { VideoPlayerProvider } from '../video-player-provider.component';

import './../../../../../test-utils/mock-resize-observer';

import { VideoFrameSegment } from './video-frame-segment.component';

it('allows the user to click on a segment', async () => {
    const labels = [getMockedLabel({ id: 'cat', name: 'cat' }), getMockedLabel({ id: 'dog', name: 'dog' })];
    const onClick = jest.fn();

    const videoFrame = getMockedVideoFrameMediaItem({});
    const selectVideoFrame = jest.fn();

    render(
        <VideoPlayerProvider selectVideoFrame={selectVideoFrame} videoFrame={videoFrame}>
            <VideoFrameSegment
                isSelectedFrame={false}
                isActiveFrame={false}
                isFilteredFrame={false}
                labels={labels}
                onClick={onClick}
                colIndex={0}
                frameNumber={0}
                showTicks={false}
                isLastFrame={false}
                isFirstFrame={false}
            />
        </VideoPlayerProvider>
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    expect(screen.getAllByRole('gridcell')).toHaveLength(labels.length);
    expect(screen.getByRole('gridcell', { name: 'Label cat in frame number 0' })).toBeInTheDocument();
    expect(screen.getByRole('gridcell', { name: 'Label dog in frame number 0' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('group'));

    expect(onClick).toHaveBeenCalledWith(videoFrame.identifier.frameNumber);
});

it('highlights selected frames', async () => {
    const labels = [getMockedLabel({ id: 'cat', name: 'cat' }), getMockedLabel({ id: 'dog', name: 'dog' })];
    const onClick = jest.fn();

    const videoFrame = getMockedVideoFrameMediaItem({});
    const selectVideoFrame = jest.fn();

    render(
        <VideoPlayerProvider selectVideoFrame={selectVideoFrame} videoFrame={videoFrame}>
            <VideoFrameSegment
                isSelectedFrame
                isActiveFrame={false}
                isFilteredFrame={false}
                labels={labels}
                onClick={onClick}
                colIndex={0}
                frameNumber={0}
                showTicks={false}
                isLastFrame={false}
                isFirstFrame={false}
            />
        </VideoPlayerProvider>
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    const selectedOverlay = screen.getByTestId('selected');
    expect(selectedOverlay).toBeInTheDocument();
});

it('highlights active frames', async () => {
    const labels = [getMockedLabel({ id: 'cat', name: 'cat' }), getMockedLabel({ id: 'dog', name: 'dog' })];
    const onClick = jest.fn();

    const videoFrame = getMockedVideoFrameMediaItem({});
    const selectVideoFrame = jest.fn();

    render(
        <VideoPlayerProvider selectVideoFrame={selectVideoFrame} videoFrame={videoFrame}>
            <VideoFrameSegment
                isSelectedFrame={false}
                isActiveFrame={true}
                isFilteredFrame={false}
                labels={labels}
                onClick={onClick}
                colIndex={0}
                frameNumber={0}
                showTicks={false}
                isLastFrame={false}
                isFirstFrame={false}
            />
        </VideoPlayerProvider>
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    const selectedOverlay = screen.getByTestId('active');
    expect(selectedOverlay).toBeInTheDocument();
});

it('highlights filtered frames', async () => {
    const labels = [getMockedLabel({ id: 'cat', name: 'cat' }), getMockedLabel({ id: 'dog', name: 'dog' })];
    const onClick = jest.fn();

    const videoFrame = getMockedVideoFrameMediaItem({});
    const selectVideoFrame = jest.fn();

    render(
        <VideoPlayerProvider selectVideoFrame={selectVideoFrame} videoFrame={videoFrame}>
            <VideoFrameSegment
                isSelectedFrame={false}
                isActiveFrame={false}
                isFilteredFrame={true}
                labels={labels}
                onClick={onClick}
                colIndex={0}
                frameNumber={0}
                showTicks={false}
                isLastFrame={false}
                isFirstFrame={false}
            />
        </VideoPlayerProvider>
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    const selectedOverlay = screen.getByTestId('active');
    expect(selectedOverlay).toBeInTheDocument();
});

it('shows the associated framenumber when showing ticks', async () => {
    const labels = [getMockedLabel({ id: 'cat', name: 'cat' }), getMockedLabel({ id: 'dog', name: 'dog' })];
    const onClick = jest.fn();

    const videoFrame = getMockedVideoFrameMediaItem({});
    const selectVideoFrame = jest.fn();

    render(
        <VideoPlayerProvider selectVideoFrame={selectVideoFrame} videoFrame={videoFrame}>
            <VideoFrameSegment
                isSelectedFrame={false}
                isActiveFrame={false}
                isFilteredFrame={true}
                labels={labels}
                onClick={onClick}
                colIndex={0}
                frameNumber={0}
                showTicks={true}
                isLastFrame={true}
                isFirstFrame={false}
            />
        </VideoPlayerProvider>
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    expect(screen.getByText(/0f/)).toBeInTheDocument();
});
