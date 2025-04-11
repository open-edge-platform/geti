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

import { CSSProperties, FC, PropsWithChildren, useEffect } from 'react';

import { TransformComponent, useControls } from 'react-zoom-pan-pinch';

import { MediaItem } from '../../../../core/media/media.interface';
import { SyncZoomState } from '../../zoom/sync-zoom-state.component';
import { useSyncScreenSize } from '../../zoom/use-sync-screen-size.hook';
import { useZoom } from '../../zoom/zoom-provider.component';

import zoomClasses from '../../zoom/transform-zoom-annotation.module.scss';

export const TransformZoom: FC<PropsWithChildren<{ mediaItem: MediaItem }>> = ({
    children,
    mediaItem,
}): JSX.Element => {
    const { resetTransform } = useControls();
    const ref = useSyncScreenSize();
    const { isPanning, isPanningDisabled, zoomTarget, screenSize, setZoomTargetOnRoi, zoomState } = useZoom();

    const style = { '--zoom-level': zoomState.zoom } as CSSProperties;
    const enableDragCursorIcon = !isPanningDisabled && isPanning;

    useEffect(() => {
        const width = mediaItem.metadata.width;
        const height = mediaItem.metadata.height;

        setZoomTargetOnRoi({ x: 0, y: 0, width, height });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [screenSize]);

    useEffect(() => {
        resetTransform();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [zoomTarget]);

    return (
        <div
            id='canvas'
            data-testid='transform-zoom-canvas'
            style={style}
            ref={ref}
            className={`${zoomClasses.canvasComponent} ${enableDragCursorIcon ? zoomClasses.isPanning : ''}`}
        >
            <SyncZoomState />
            <TransformComponent wrapperClass={zoomClasses.transformWrapper} contentClass={zoomClasses.transformContent}>
                {children}
            </TransformComponent>
        </div>
    );
};
