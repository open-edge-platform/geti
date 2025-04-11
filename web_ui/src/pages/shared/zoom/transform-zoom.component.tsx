// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { CSSProperties, PointerEvent, ReactNode } from 'react';

import { useHotkeys } from 'react-hotkeys-hook';
import { TransformComponent, useControls } from 'react-zoom-pan-pinch';

import { useAnnotatorHotkeys } from '../../annotator/hooks/use-hotkeys-configuration.hook';
import { PointerType } from '../../annotator/tools/tools.interface';
import { useSyncScreenSize } from '../../annotator/zoom/use-sync-screen-size.hook';
import { useZoom } from '../../annotator/zoom/zoom-provider.component';
import { isLeftButton, isWheelButton } from '../../buttons-utils';

import classes from './transform-zoom.module.scss';

/*
    This component is responsible for:

    - Keeping the 'react-zoom-pan-pinch' zoomState in sync with the ZoomProvider
    - Update the zoom state if the target or screenSize change
*/

export const TransformZoom = ({ children }: { children?: ReactNode }): JSX.Element => {
    const { hotkeys } = useAnnotatorHotkeys();

    const { resetTransform } = useControls();

    const ref = useSyncScreenSize();
    const { setIsPanningDisabled, isPanning, isPanningDisabled, setIsDblClickDisabled, isDblCLickDisabled, zoomState } =
        useZoom();

    const style = { '--zoom-level': zoomState.zoom } as CSSProperties;
    const enableDragCursorIcon = !isPanningDisabled && isPanning;

    const handlePointerDown = (event: PointerEvent<HTMLDivElement>) => {
        const isPressingPanningHotkeys = (isLeftButton(event) && event.ctrlKey) || isWheelButton(event);

        if (
            (isPressingPanningHotkeys || event.pointerType === PointerType.Touch) &&
            event.pointerType !== PointerType.Pen
        ) {
            setIsPanningDisabled(false);
        } else {
            setIsPanningDisabled(true);
        }

        return;
    };

    const handlePointerUp = (event: PointerEvent<HTMLDivElement>): void => {
        if (event.pointerType === PointerType.Pen) {
            !isDblCLickDisabled && setIsDblClickDisabled(true);
        } else {
            isDblCLickDisabled && setIsDblClickDisabled(false);
        }
    };

    useHotkeys(
        hotkeys.zoom,
        (event) => {
            event.preventDefault();

            resetTransform();
        },
        [resetTransform]
    );

    return (
        <div
            id='canvas'
            data-testid='transform-zoom-canvas'
            style={style}
            ref={ref}
            className={`${classes.canvasComponent} ${enableDragCursorIcon ? classes.isPanning : ''}`}
            onPointerDown={handlePointerDown}
            onPointerUp={handlePointerUp}
        >
            <TransformComponent wrapperClass={classes.transformWrapper} contentClass={classes.transformContent}>
                {children}
            </TransformComponent>
        </div>
    );
};
