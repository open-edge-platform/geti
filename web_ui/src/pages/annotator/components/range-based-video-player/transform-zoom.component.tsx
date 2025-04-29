// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
