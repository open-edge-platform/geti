// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from 'react';

import type { DatasetSubset, Media, MediaOmePlane, OmeImageInfo } from '@/api/types';
import { Key, View } from '@geti-ui/ui';
import { useSpinDelay } from 'spin-delay';

import { AnnotatorCanvas } from '../../../modules/annotator/annotator-canvas/annotator-canvas';
import type { AnnotatorMode } from '../../../modules/annotator/annotator-mode';
import { useIsFetchingPredictions } from '../../../modules/annotator/api/use-media-predictions';
import { useSelectedMediaItem } from '../../../modules/annotator/selected-media-item-provider.component';
import { BottomToolbar } from '../../../modules/annotator/shell/bottom-toolbar/bottom-toolbar.component';
import { PrimaryToolbar } from '../../../modules/annotator/shell/primary-toolbar/primary-toolbar.component';
import { AnnotatorCanvasSettings } from '../../../modules/annotator/shell/primary-toolbar/settings/annotator-canvas-settings.component';
import { useNextMediaPrefetch } from '../../../modules/annotator/shell/utils';
import { ToolManagerProvider } from '../../../modules/annotator/tools/tool-manager-provider.component';
import { ToolOptions } from '../../../modules/annotator/tools/tool-options/tool-options.component';
import { VideoPlayerProvider } from '../../../modules/annotator/video-player/video-player-provider.component';
import { getMediaItemKey, isOmeImage, isOmePlane } from '../../../shared/media-item-utils';
import { SecondaryToolbar } from '../media-preview/secondary-toolbar/secondary-toolbar.component';
import { useNextPredictionPrefetch } from '../media-preview/use-next-prediction-prefetch.hook';
import { useAnnotatedOmePlanes, useOmeChannelView } from './api/use-ome-image';
import { OmeNavigationToolbar } from './ome-navigation-toolbar/ome-navigation-toolbar.component';
import { getRenderVersion } from './ome-render.utils';

const DATASET_SUBSETS: DatasetSubset[] = ['unassigned', 'training', 'validation', 'testing'];

const isDatasetSubset = (key: Key | null): key is DatasetSubset => DATASET_SUBSETS.includes(key as DatasetSubset);

const useSubset = (subset: DatasetSubset, mediaItem: Media) => {
    const mediaItemKey = getMediaItemKey(mediaItem);
    const [pendingSubset, setPendingSubset] = useState<DatasetSubset>(subset);
    const [prev, setPrev] = useState({ mediaItemKey, subset });

    if (prev.mediaItemKey !== mediaItemKey || prev.subset !== subset) {
        setPrev({ mediaItemKey, subset });
        setPendingSubset(subset);
    }

    const changeSubset = (key: Key | null) => {
        if (isDatasetSubset(key)) {
            setPendingSubset(key);
        }
    };

    return {
        currentSubset: pendingSubset,
        changeCurrentSubset: changeSubset,
        isReadOnlySubset: pendingSubset === subset && subset !== 'unassigned',
    };
};

// Re-renders the displayed plane whenever its channel display settings change, without leaving the plane
const useSyncRenderVersion = (plane: MediaOmePlane) => {
    const { setMediaItem } = useSelectedMediaItem();
    const { data: channelView } = useOmeChannelView(plane.id);
    const renderVersion = channelView === undefined ? undefined : getRenderVersion(channelView.settings);

    useEffect(() => {
        if (renderVersion !== undefined && renderVersion !== plane.render_version) {
            setMediaItem({ ...plane, render_version: renderVersion });
        }
    }, [plane, renderVersion, setMediaItem]);
};

const NextPredictionPrefetch = ({ nextMediaItem }: { nextMediaItem: Media }) => {
    useNextPredictionPrefetch(nextMediaItem);

    return null;
};

type OmeAnnotatorProps = {
    info: OmeImageInfo;
    image: ImageData;
    plane: MediaOmePlane;
    items: Media[];
    mode: AnnotatorMode;
    onChangeAnnotatorMode: (mode: AnnotatorMode) => void;
    onClose: () => void;
    onSelectedMediaItem: (item: Media) => void;
    subset: DatasetSubset;
    isUserReviewed: boolean;
};

const OmeAnnotator = ({
    info,
    plane,
    image,
    mode,
    items,
    onClose,
    subset,
    isUserReviewed,
    onSelectedMediaItem,
    onChangeAnnotatorMode,
}: OmeAnnotatorProps) => {
    const isAnnotationMode = mode === 'annotation';
    const isPredictionMode = mode === 'prediction';

    const { nextMediaItem } = useNextMediaPrefetch(plane, items);
    const { currentSubset, changeCurrentSubset, isReadOnlySubset } = useSubset(subset, plane);
    const isLoadingPredictions = useIsFetchingPredictions(plane.id) && isPredictionMode;
    const { data: annotatedPlanes = [] } = useAnnotatedOmePlanes(plane.id);

    const isLoadingPredictionsDelayed = useSpinDelay(isLoadingPredictions, { delay: 400, minDuration: 200 });

    useSyncRenderVersion(plane);

    const selectPlane = (z: number, t: number) => {
        if (z !== plane.z_index || t !== plane.t_index) {
            onSelectedMediaItem({ ...plane, z_index: z, t_index: t });
        }
    };

    const selectNextMediaItem = async () => {
        if (nextMediaItem !== undefined) {
            onSelectedMediaItem(nextMediaItem);
        }
    };

    return (
        <>
            {isPredictionMode && nextMediaItem && !isOmeImage(nextMediaItem) && (
                <NextPredictionPrefetch nextMediaItem={nextMediaItem} />
            )}
            <View gridArea={'header'}>
                <SecondaryToolbar
                    mode={mode}
                    items={items}
                    onClose={onClose}
                    mediaItem={plane}
                    onSelectedMediaItem={onSelectedMediaItem}
                    onModeChange={onChangeAnnotatorMode}
                    onSelectNextMediaItem={selectNextMediaItem}
                    subset={currentSubset}
                    hasSubsetChanged={currentSubset !== subset}
                    isLoadingPredictions={isLoadingPredictions}
                />
            </View>

            {isAnnotationMode && (
                <View gridArea={'toolbar'} aria-label={'primary toolbar'}>
                    <PrimaryToolbar />
                </View>
            )}

            <View gridArea={'navigation-toolbar'}>
                <OmeNavigationToolbar
                    info={info}
                    plane={plane}
                    annotatedPlanes={annotatedPlanes}
                    onSelectPlane={selectPlane}
                />
            </View>

            <View gridArea={'bottom'}>
                <BottomToolbar
                    isUserReviewed={isUserReviewed}
                    subset={currentSubset}
                    onSubsetChange={changeCurrentSubset}
                    mediaItem={plane}
                    isReadOnlySubset={isReadOnlySubset}
                />
            </View>

            <View gridArea={'canvas'} overflow={'hidden'} position={'relative'}>
                <AnnotatorCanvasSettings>
                    <AnnotatorCanvas
                        isLoadingPredictions={isLoadingPredictionsDelayed}
                        mediaItem={plane}
                        image={image}
                        mode={mode}
                        isReadOnly={isPredictionMode}
                    />
                </AnnotatorCanvasSettings>
                {isAnnotationMode && <ToolOptions />}
            </View>
        </>
    );
};

type OmeAnnotatorContainerProps = {
    info: OmeImageInfo;
    mode: AnnotatorMode;
    changeAnnotatorMode: (mode: AnnotatorMode) => void;
    onClose: () => void;
    items: Media[];
    onSelectedMediaItem: (item: Media) => void;
    subset: DatasetSubset;
    isUserReviewed: boolean;
};

export const OmeAnnotatorContainer = ({
    info,
    mode,
    changeAnnotatorMode,
    onClose,
    items,
    subset,
    isUserReviewed,
    onSelectedMediaItem,
}: OmeAnnotatorContainerProps) => {
    const { mediaItem, image } = useSelectedMediaItem();

    if (!isOmePlane(mediaItem)) {
        return null;
    }

    // Annotator parts shared with videos read the (absent) video player context
    return (
        <VideoPlayerProvider videoFrame={undefined} changeSelectedMediaItem={onSelectedMediaItem}>
            <ToolManagerProvider>
                <OmeAnnotator
                    info={info}
                    mode={mode}
                    subset={subset}
                    items={items}
                    image={image}
                    onClose={onClose}
                    plane={mediaItem}
                    isUserReviewed={isUserReviewed}
                    onChangeAnnotatorMode={changeAnnotatorMode}
                    onSelectedMediaItem={onSelectedMediaItem}
                />
            </ToolManagerProvider>
        </VideoPlayerProvider>
    );
};
