// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { isEqual } from 'lodash-es';
import { useControls, useTransformEffect } from 'react-zoom-pan-pinch';

import { usePrevious } from '../../../hooks/use-previous/use-previous.hook';
import { useSelectedMediaItem } from '../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useZoom } from './zoom-provider.component';

export const SyncZoomTarget = () => {
    const { setZoomTargetOnRoi, getZoomStateForTarget } = useZoom();
    const { selectedMediaItem } = useSelectedMediaItem();

    const previousSelectedMediaItem = usePrevious(selectedMediaItem);

    const { setTransform } = useControls();

    // Everytime the user changes images, we adjust the zoomTarget
    useEffect(() => {
        if (
            !isEqual(selectedMediaItem?.identifier, previousSelectedMediaItem?.identifier) &&
            selectedMediaItem !== undefined
        ) {
            const imageTarget = {
                x: 0,
                y: 0,
                width: selectedMediaItem.image.width,
                height: selectedMediaItem.image.height,
            };
            setZoomTargetOnRoi(imageTarget);

            const {
                zoom,
                translation: { x, y },
            } = getZoomStateForTarget(imageTarget);

            setTransform(x, y, zoom, 200);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedMediaItem, previousSelectedMediaItem, setZoomTargetOnRoi]);

    return <></>;
};

/*
    This component is responsible for:

    - Reset the zoomState if the selectedMedia changes
    - Reset the zoomState if the selectedTask is a global task
    - Zoom in on the annotation if the selectedTask is a local task
*/
export const SyncZoomState = (): JSX.Element => {
    const { zoomTarget, getZoomStateForTarget, screenSize, zoomState, setZoomState } = useZoom();

    const { setTransform } = useControls();

    useTransformEffect(({ state }) => {
        const { scale, positionY, positionX } = state;

        if (scale !== zoomState.zoom) {
            setZoomState(() => ({
                zoom: scale,
                translation: {
                    x: positionX,
                    y: positionY,
                },
            }));
        }
    });

    // Everytime the target changes, we need to adjust the zoom level
    const previousZoomTarget = usePrevious(zoomTarget);
    useEffect(() => {
        if (
            zoomTarget &&
            zoomTarget.width !== 0 &&
            zoomTarget.height !== 0 &&
            zoomTarget.width !== previousZoomTarget?.width &&
            zoomTarget.height !== previousZoomTarget?.height
        ) {
            const {
                zoom,
                translation: { x, y },
            } = getZoomStateForTarget(zoomTarget);

            setTransform(x, y, zoom, 200);
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [getZoomStateForTarget, zoomTarget]);

    // Reset zoom if screen size changes
    useEffect(() => {
        if (zoomTarget !== previousZoomTarget) {
            return;
        }

        if (screenSize !== undefined && zoomTarget !== undefined) {
            const {
                zoom,
                translation: { x, y },
            } = getZoomStateForTarget(zoomTarget);

            setTransform(x, y, zoom, 200);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [screenSize, zoomTarget, previousZoomTarget]);

    return <></>;
};
