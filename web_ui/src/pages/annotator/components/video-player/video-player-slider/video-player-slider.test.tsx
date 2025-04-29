// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import '@wessberg/pointer-events';

import { ReactNode } from 'react';

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';
import range from 'lodash/range';

import { MEDIA_TYPE } from '../../../../../core/media/base-media.interface';
import { getMockedVideoFrameMediaItem } from '../../../../../test-utils/mocked-items-factory/mocked-media';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { hover, unhover } from '../../../../../test-utils/utils';
import { ProjectProvider } from '../../../../project-details/providers/project-provider/project-provider.component';
import { TaskProvider } from '../../../providers/task-provider/task-provider.component';
import { VideoPlayerSlider as Slider } from './video-player-slider.component';

jest.mock('../../../hooks/use-dataset-identifier.hook', () => ({
    useDatasetIdentifier: () => ({ workspaceId: 'workspace-id', projectId: 'project-id', datasetId: 'dataset-id' }),
}));

describe('Video player slider', () => {
    afterAll(() => {
        jest.clearAllMocks();
        jest.clearAllTimers();
        jest.useRealTimers();
    });

    const selectFrame = jest.fn();
    const videoFrame = getMockedVideoFrameMediaItem({});
    const step = videoFrame.metadata.frameStride;
    const videoFrames = range(0, videoFrame.metadata.frames + 1, step).map((frameNumber) => {
        return { ...videoFrame, identifier: { ...videoFrame.identifier, frameNumber } };
    });

    const sliderWidth = 1000;

    const projectRender = async (component: ReactNode) => {
        render(
            <ProjectProvider
                projectIdentifier={{
                    projectId: 'project-id',
                    workspaceId: 'workspace-id',
                    organizationId: 'organization-id',
                }}
            >
                <TaskProvider>{component}</TaskProvider>
            </ProjectProvider>
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    beforeEach(() => {
        Element.prototype.getBoundingClientRect = jest.fn(() => {
            return {
                width: sliderWidth,
                height: 20,
                x: 0,
                y: 0,
                top: 0,
                left: 0,
                bottom: 0,
                right: 0,
                DOMRect: null,
                toJSON: () => null,
            };
        });
    });

    it('Selects a video frame when changing the slider value', async () => {
        await projectRender(
            <Slider
                isInActiveMode={false}
                restrictedVideoFrames={videoFrames.map(({ identifier: { frameNumber } }) => frameNumber)}
                mediaItem={videoFrame}
                selectFrame={selectFrame}
                step={step}
                minValue={0}
                maxValue={videoFrames[videoFrames.length - 1].identifier.frameNumber}
            />
        );

        const slider = screen.getByRole('slider');
        expect(slider).toBeInTheDocument();
        expect(slider).toHaveAttribute('min', '0');
        expect(slider).toHaveAttribute('max', `${videoFrame.metadata.frames}`);
        expect(slider).toHaveValue(`${videoFrame.identifier.frameNumber}`);

        fireEvent.keyDown(slider, { key: 'Right' });
        expect(selectFrame).toHaveBeenCalledWith(step);
    });

    it('Renders a frame in the middle', async () => {
        jest.useFakeTimers();

        const middleVideoFrame = getMockedVideoFrameMediaItem({
            identifier: {
                type: MEDIA_TYPE.VIDEO_FRAME,
                videoId: 'video',
                frameNumber: 180,
            },
        });
        await projectRender(
            <Slider
                isInActiveMode={false}
                restrictedVideoFrames={videoFrames.map(({ identifier: { frameNumber } }) => frameNumber)}
                mediaItem={middleVideoFrame}
                selectFrame={selectFrame}
                step={step}
                minValue={0}
                maxValue={videoFrames[videoFrames.length - 1].identifier.frameNumber}
            />
        );

        const slider = screen.getByRole('slider');
        expect(slider).toBeInTheDocument();
        expect(slider).toHaveAttribute('min', '0');
        expect(slider).toHaveAttribute('max', `${middleVideoFrame.metadata.frames}`);
        expect(slider).toHaveValue(`${middleVideoFrame.identifier.frameNumber}`);

        // Simulate hover
        hover(slider);

        // Simulate mouse movement with clientX
        fireEvent.mouseMove(slider, { clientX: sliderWidth / 10 });

        jest.advanceTimersByTime(1000);

        expect(
            screen.getByRole('img', { name: `Thumbnail for frame ${middleVideoFrame.metadata.frames / 10}` })
        ).toBeInTheDocument();

        // Simulate unhover
        unhover(slider);
        expect(screen.queryByRole('img')).not.toBeInTheDocument();

        jest.useRealTimers();
    });
});
