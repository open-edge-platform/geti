// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { renderHook } from '@testing-library/react';

import { useVideoPlayer, VideoPlayerContextProps } from '../video-player-provider.component';
import { useVideoControlsWithSaveConfirmation } from './use-video-controls-with-save-confirmation.hook';

const mockedControls = {
    goto: jest.fn(),
    next: jest.fn(),
    play: jest.fn(),
    previous: jest.fn(),
};
jest.mock('../video-player-provider.component', () => ({
    ...jest.requireActual('../video-player-provider.component'),
    useVideoPlayer: jest.fn(),
}));

const mockedExplanationVisible = jest.fn();
jest.mock('../../../providers/prediction-provider/prediction-provider.component', () => ({
    ...jest.requireActual('../../../providers/prediction-provider/prediction-provider.component'),
    usePrediction: () => ({ setExplanationVisible: mockedExplanationVisible }),
}));

const mockedConfirmSaveAnnotations = jest.fn((callback) => callback());
jest.mock('../../../providers/submit-annotations-provider/submit-annotations-provider.component', () => ({
    ...jest.requireActual('../../../providers/submit-annotations-provider/submit-annotations-provider.component'),
    useSubmitAnnotations: () => ({
        confirmSaveAnnotations: mockedConfirmSaveAnnotations,
    }),
}));

describe('useVideoControlsWithSaveConfirmation', () => {
    beforeEach(() => {
        jest.clearAllMocks();

        jest.mocked(useVideoPlayer).mockReturnValue({
            videoControls: mockedControls,
        } as unknown as VideoPlayerContextProps);
    });

    it('call play control and sets explanation to false', () => {
        const { result } = renderHook(() => useVideoControlsWithSaveConfirmation());

        result.current.play && result.current.play();

        expect(mockedControls.play).toHaveBeenCalled();
        expect(mockedExplanationVisible).toHaveBeenCalledWith(false);
        expect(mockedConfirmSaveAnnotations).toHaveBeenCalled();
    });

    it('control "play" is falsy', () => {
        jest.mocked(useVideoPlayer).mockReturnValue({
            videoControls: { play: undefined },
        } as unknown as VideoPlayerContextProps);

        const { result } = renderHook(() => useVideoControlsWithSaveConfirmation());

        result.current.play && result.current.play();

        expect(mockedExplanationVisible).not.toHaveBeenCalled();
        expect(mockedConfirmSaveAnnotations).toHaveBeenCalled();
    });

    it('call next control', () => {
        const { result } = renderHook(() => useVideoControlsWithSaveConfirmation());

        result.current.next && result.current.next();

        expect(mockedControls.next).toHaveBeenCalled();
        expect(mockedConfirmSaveAnnotations).toHaveBeenCalled();
    });

    it('call previous control', () => {
        const { result } = renderHook(() => useVideoControlsWithSaveConfirmation());

        result.current.previous && result.current.previous();

        expect(mockedControls.previous).toHaveBeenCalled();
        expect(mockedConfirmSaveAnnotations).toHaveBeenCalled();
    });

    it('call goto control', () => {
        const { result } = renderHook(() => useVideoControlsWithSaveConfirmation());
        const frameNumber = 1;
        result.current.goto && result.current.goto(frameNumber);

        expect(mockedControls.goto).toHaveBeenCalledWith(frameNumber);
        expect(mockedConfirmSaveAnnotations).toHaveBeenCalled();
    });
});
