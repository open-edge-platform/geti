// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    createContext,
    Dispatch,
    MutableRefObject,
    ReactNode,
    RefObject,
    SetStateAction,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useRef,
    useState,
} from 'react';

import { VisuallyHidden } from '@adobe/react-spectrum';
import { MissingProviderError } from '@shared/missing-provider-error';

import { mediaIdentifierToString, MediaItem } from '../../../../../core/media/media.interface';
import { isVideoFrame, VideoFrame } from '../../../../../core/media/video.interface';
import { usePrevious } from '../../../../../hooks/use-previous/use-previous.hook';
import { useAnnotatorMode } from '../../../hooks/use-annotator-mode';
import { useSelectedMediaItem } from '../../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { Video } from '../video.component';
import { VideoControls } from './../video-controls/video-controls.interface';
import {
    useVideoPlayerContext,
    VideoPlayerContext,
    VideoPlayerContextProps,
} from './../video-player-provider.component';
import { BufferVideoPredictions } from './buffer-video-predictions.component';
import { VideoPlayerErrorReason } from './streaming-video-player.interface';
import { useBufferStreamingQueries } from './use-buffer-streaming-queries.hook';
import { BufferRange } from './utils';

export interface VideoPlayerPlayerContextProps {
    videoRef: RefObject<HTMLVideoElement>;
    isPlaying: boolean;
    setIsPlaying: Dispatch<SetStateAction<boolean>>;
    currentIndex: number;
    setCurrentIndex: Dispatch<SetStateAction<number>>;

    // TODO: these are temporary settings that we use to test performance once
    // we've figured out good heuristics for these values depending on the
    // playback rate and the frameskip we will likely remove these
    neighbourSize: number;
    setNeighbourSize: (rate: number) => void;

    // Settings related to how the user plays the video
    isMuted: boolean;
    setIsMuted: (muted: boolean) => void;
    playbackRate: number;
    setPlaybackRate: (rate: number) => void;
    videoPlayerError: VideoPlayerErrorReason | undefined;
    setVideoPlayerError: (reason: VideoPlayerErrorReason | undefined) => void;
    isBuffering: boolean;
    buffers: BufferRange[];
}

const StreamingVideoPlayerContext = createContext<VideoPlayerPlayerContextProps | undefined>(undefined);
interface StreamingVideoPlayerProviderProps {
    children: ReactNode;
    mediaItem: VideoFrame | undefined;
}

interface useResumeVideoProps {
    isPlaying: boolean;
    videoRef: RefObject<HTMLVideoElement>;
    videoPausedBySystem: MutableRefObject<boolean>;
}

const useResumeVideo = ({ isPlaying, videoRef, videoPausedBySystem }: useResumeVideoProps) => {
    const { selectedMediaItemQuery } = useSelectedMediaItem();

    useEffect(() => {
        if (!isPlaying && !selectedMediaItemQuery.isFetching && videoPausedBySystem.current) {
            videoRef.current && videoRef.current.play();
            videoPausedBySystem.current = false;
        }
    }, [videoPausedBySystem, isPlaying, selectedMediaItemQuery.isFetching, videoRef]);
};

export const StreamingVideoPlayerProvider = ({ children, mediaItem }: StreamingVideoPlayerProviderProps) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const videoPausedBySystem = useRef(false);
    const { currentMode } = useAnnotatorMode();

    const [isMuted, setIsMuted] = useState(true);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isBuffering, setIsBuffering] = useState(true);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [playbackRate, setPlaybackRate] = useState(1.0);
    const [neighbourSize, setNeighbourSize] = useState(5);
    const [videoPlayerError, setVideoPlayerError] = useState<VideoPlayerErrorReason>();
    const previousMediaItem = usePrevious(mediaItem);

    const oldContext = useVideoPlayerContext();
    const previousVideoFrame = previousMediaItem?.identifier.frameNumber;
    const isNotAVideoFrame = mediaItem === undefined || !isVideoFrame(mediaItem);

    const { buffers, setBuffers, nextBuffer } = useBufferStreamingQueries(
        mediaItem,
        isPlaying ? currentIndex : (mediaItem?.identifier.frameNumber ?? currentIndex),
        playbackRate,
        neighbourSize
    );

    useResumeVideo({ isPlaying, videoRef, videoPausedBySystem });

    useEffect(() => {
        if (mediaItem?.identifier.videoId === previousMediaItem?.identifier.videoId) {
            return;
        }

        setVideoPlayerError(undefined);
        setIsMuted(true);
        setPlaybackRate(1.0);
        setIsPlaying(false);
    }, [mediaItem, previousMediaItem]);

    useEffect(() => {
        if (mediaItem === undefined) {
            return;
        }

        if (previousVideoFrame !== mediaItem.identifier.frameNumber) {
            const fps = mediaItem.metadata.fps;

            setCurrentIndex(mediaItem.identifier.frameNumber);

            if (videoRef.current !== null) {
                const currentTime = (mediaItem.identifier.frameNumber + 1) / fps;

                videoRef.current.currentTime = isNaN(currentTime) ? 0 : currentTime;
            }
        }
    }, [mediaItem, previousVideoFrame, videoRef]);

    useEffect(() => {
        if (!videoRef.current) {
            return;
        }

        const oldPlaybackRate = videoRef.current.playbackRate;

        try {
            videoRef.current.playbackRate = playbackRate;
        } catch (_error: unknown) {
            setPlaybackRate(oldPlaybackRate);
        }
    }, [playbackRate]);

    const playingVideoFrame = useMemo((): VideoFrame | undefined => {
        if (isNotAVideoFrame) {
            return undefined;
        }

        return { ...mediaItem, identifier: { ...mediaItem.identifier, frameNumber: currentIndex } };
    }, [currentIndex, mediaItem, isNotAVideoFrame]);

    const goto = useCallback(
        (newFrameNumber: number, isPauseHandler = false) => {
            if (mediaItem === undefined) {
                return;
            }

            if (newFrameNumber >= mediaItem.metadata.frames) {
                return;
            }

            setCurrentIndex(newFrameNumber);

            // Update video element
            if (videoRef.current) {
                if (isPlaying) {
                    videoRef.current.pause();

                    if (!isPauseHandler) {
                        videoPausedBySystem.current = true;
                    }
                }

                const fps = mediaItem.metadata.frameStride;
                videoRef.current.currentTime = (newFrameNumber + 1) / fps;
            }

            const step = oldContext?.step ?? 1;
            const nearest = Math.min(Math.round(newFrameNumber / step) * step, mediaItem.metadata.frames - 1);

            oldContext?.videoControls.goto(nearest);
        },
        [isPlaying, oldContext?.step, oldContext?.videoControls, mediaItem]
    );

    const videoPlayerContext = useMemo(() => {
        if (isNotAVideoFrame || oldContext === undefined) {
            return oldContext;
        }

        const videoControls: VideoControls = {
            ...oldContext?.videoControls,
            isPlaying,
            goto,
            play: () => {
                videoRef.current?.play().catch((e) => {
                    console.warn("Couldn't play video", e);
                });
            },
            pause: () => {
                setIsPlaying(false);
                videoPausedBySystem.current = false;
                videoRef.current?.pause();

                const step = oldContext.step;
                const maxNearest = Math.floor((mediaItem.metadata.frames - 1) / step) * step;
                const nearest = Math.min(Math.round(currentIndex / step) * step, maxNearest);

                goto(nearest, true);
            },
            previous: () => {
                if (!isPlaying) {
                    oldContext.videoControls.previous();
                    return;
                }

                if (videoRef.current) {
                    videoRef.current.currentTime -= 1.0;
                }
            },
            next: () => {
                if (!isPlaying) {
                    oldContext.videoControls.next();
                    return;
                }

                if (videoRef.current) {
                    videoRef.current.currentTime += 1.0;
                }
            },
        };

        return {
            ...oldContext,
            videoControls,
            videoFrame: playingVideoFrame,
        } as VideoPlayerContextProps;
    }, [isPlaying, playingVideoFrame, oldContext, currentIndex, goto, mediaItem?.metadata?.frames, isNotAVideoFrame]);

    const value = {
        videoRef,
        isPlaying,
        setIsPlaying,
        currentIndex,
        setCurrentIndex,

        videoPlayerError,
        setVideoPlayerError,
        playbackRate,
        setPlaybackRate,

        // TMP (used to debug settings)
        neighbourSize,
        setNeighbourSize,

        isMuted,
        setIsMuted,
        isBuffering,
        buffers,
    };

    const handlePause = () => setIsPlaying(false);
    const handlePlay = () => setIsPlaying(true);
    const handleBuffering = () => setIsBuffering(true);
    const handleBufferingFinished = () => setIsBuffering(false);
    const handleEnded = () => {
        if (!videoRef.current) {
            return;
        }

        videoRef.current.currentTime = 0;
    };

    return (
        <StreamingVideoPlayerContext.Provider value={value}>
            <VideoPlayerContext.Provider value={videoPlayerContext}>
                {videoPlayerContext !== undefined && oldContext !== undefined && mediaItem !== undefined && (
                    <>
                        {/* We hide the video element as we're only using it to load the video stream 
                            once the user starts playing the video we use a requestVideoFrameCallback
                            listener to update the canvas with the current frame's image */}
                        <VisuallyHidden>
                            <Video
                                key={mediaItem.identifier.videoId}
                                id={mediaIdentifierToString(mediaItem.identifier)}
                                videoRef={videoRef}
                                videoFrame={mediaItem}
                                muted={isMuted}
                                onLoad={handlePause}
                                onPause={handlePause}
                                onPlay={handlePlay}
                                onSeeking={handleBuffering}
                                onSeeked={handleBufferingFinished}
                                onWaiting={handleBuffering}
                                onCanPlay={handleBufferingFinished}
                                onCanPlayThrough={handleBufferingFinished}
                                onEnded={handleEnded}
                                onError={({ currentTarget }) => {
                                    setVideoPlayerError(currentTarget.error?.code);
                                }}
                                onAbort={(error) => {
                                    console.error('VideoPlayer abort', error);
                                }}
                                preload='auto'
                            />
                        </VisuallyHidden>
                        {nextBuffer !== undefined && (
                            <BufferVideoPredictions
                                mode={currentMode}
                                nextBuffer={nextBuffer}
                                setBuffers={setBuffers}
                                videoFrame={mediaItem}
                            />
                        )}
                    </>
                )}

                {children}
            </VideoPlayerContext.Provider>
        </StreamingVideoPlayerContext.Provider>
    );
};

export const useStreamingVideoPlayer = (): VideoPlayerPlayerContextProps => {
    const context = useContext(StreamingVideoPlayerContext);

    if (context === undefined) {
        throw new MissingProviderError('useStreamingVideoPlayer', 'StreamingVideoPlayerProvider');
    }

    return context;
};

export const useStreamingVideoPlayerContext = (): VideoPlayerPlayerContextProps | undefined => {
    return useContext(StreamingVideoPlayerContext);
};

export const useIsStreamingVideoPlayerEnabled = (
    selectedMediaItem: MediaItem | undefined
): selectedMediaItem is VideoFrame => {
    const ctx = useContext(StreamingVideoPlayerContext);

    return ctx !== undefined && selectedMediaItem !== undefined && isVideoFrame(selectedMediaItem);
};
