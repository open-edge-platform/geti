// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useRef } from 'react';

import { Invisible, Visible } from '../../../../../assets/icons';
import { RegionOfInterest } from '../../../../../core/annotations/annotation.interface';
import { KeypointNode } from '../../../../../core/annotations/shapes.interface';
import { useEventListener } from '../../../../../hooks/event-listener/event-listener.hook';
import { MouseEvents } from '../../../../../shared/mouse-events';
import { ExpandablePointLabel } from '../../../../create-project/components/pose-template/canvas/expandable-point-label.component';
import { getPointInRoi } from '../../../../utils';
import { PoseKeypointVisibility } from '../../../annotation/shapes/pose-keypoints.component';
import { useAnnotatorCanvasSettings } from '../../../providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component';
import { useAnnotatorContextMenu } from '../../../providers/annotator-context-menu-provider/annotator-context-menu-provider.component';
import { useZoom } from '../../../zoom/zoom-provider.component';
import { ResizeAnchor } from '../resize-anchor.component';
import { ResizeAnchorType } from '../resize-anchor.enum';

interface EditPosePointToolProps {
    roi: RegionOfInterest;
    point: KeypointNode;
    isLabelVisible: boolean;
    onStart?: () => void;
    onToggleVisibility: () => void;
    onComplete: () => void;
    moveAnchorTo: (x: number, y: number) => void;
}

const CONTEXT_ID = 'Keypoint context menu';

const isResizeKeypointElement = (element: HTMLElement) => {
    return /^Resize keypoint|cross bold icon/.test(element.getAttribute('aria-label') ?? '');
};

const getContextOption = (isVisible: boolean) => {
    return isVisible
        ? { icon: <Invisible />, title: 'Mark as occluded' }
        : { icon: <Visible />, title: 'Mark as visible' };
};

export const EditPosePoint = ({
    roi,
    point,
    isLabelVisible,
    onStart,
    onComplete,
    moveAnchorTo,
    onToggleVisibility,
}: EditPosePointToolProps) => {
    const { zoomState } = useZoom();
    const containerRef = useRef<SVGGElement | null>(null);
    const { showContextMenu, hideContextMenu, contextConfig } = useAnnotatorContextMenu();

    const { canvasSettingsState } = useAnnotatorCanvasSettings();
    const [canvasSettings] = canvasSettingsState;

    const showLabels =
        Boolean(canvasSettings.hideLabels.value) === false && Number(canvasSettings.labelOpacity.value) > 0;

    useEventListener(
        MouseEvents.ContextMenu,
        (event) => {
            event.preventDefault();

            if (isResizeKeypointElement(event.target as HTMLElement)) {
                showContextMenu({
                    menuPosition: { top: event.clientY, left: event.clientX },
                    menuItems: [{ id: 'Point visible', children: [getContextOption(point.isVisible)] }],
                    contextId: CONTEXT_ID,
                    ariaLabel: 'Point visible',
                    handleMenuAction: onToggleVisibility,
                });
                return;
            }

            if (contextConfig.contextId === CONTEXT_ID) {
                hideContextMenu();
            }
        },
        containerRef
    );

    return (
        <g style={{ pointerEvents: 'auto' }} ref={containerRef}>
            <foreignObject height={'100%'} width={'100%'} overflow={'visible'} style={{ pointerEvents: 'none' }}>
                <ExpandablePointLabel point={point} isVisible={isLabelVisible && showLabels} />
            </foreignObject>

            <ResizeAnchor
                y={point.y}
                x={point.x}
                zoom={zoomState.zoom}
                onStart={onStart}
                onComplete={onComplete}
                cursor={'crosshair'}
                label={`Resize keypoint ${point.label.name} anchor`}
                moveAnchorTo={(x, y) => {
                    const pointInRoi = getPointInRoi({ x, y }, roi);
                    moveAnchorTo(pointInRoi.x, pointInRoi.y);
                }}
                type={ResizeAnchorType.CUSTOM}
                Anchor={<PoseKeypointVisibility point={point} />}
            />
        </g>
    );
};
