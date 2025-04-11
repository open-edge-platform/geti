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

import { PointerEvent, RefObject, useEffect, useRef, useState } from 'react';

import isEmpty from 'lodash/isEmpty';
import noop from 'lodash/noop';

import { Delete } from '../../../../../assets/icons';
import { Point, Polygon } from '../../../../../core/annotations/shapes.interface';
import { useEventListener } from '../../../../../hooks/event-listener/event-listener.hook';
import { KeyboardEvents } from '../../../../../shared/keyboard-events/keyboard.interface';
import { MouseEvents } from '../../../../../shared/mouse-events/mouse.interface';
import { isLeftButton } from '../../../../buttons-utils';
import { isKeyboardDelete } from '../../../../media/utils';
import { getRelativePoint, projectPointOnLine } from '../../../../utils';
import { useAnnotationScene } from '../../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { useAnnotatorContextMenu } from '../../../providers/annotator-context-menu-provider/annotator-context-menu-provider.component';
import { ANCHOR_SIZE, ResizeAnchor } from '../resize-anchor.component';
import { selectAnchorPointLabel } from './utils';

interface EditPointsProps {
    zoom: number;
    shape: Polygon;
    onComplete: () => void;
    roi: { width: number; height: number };
    removePoints: (indexes: number[]) => void;
    addPoint: (idx: number, x: number, y: number) => void;
    moveAnchorTo: (idx: number, x: number, y: number) => void;
}

interface GhostPoint {
    idx: number;
    point: Point;
}

const CONTEXT_ID = 'Delete point';

export const EditPoints = ({
    roi,
    zoom,
    shape,
    addPoint,
    onComplete,
    moveAnchorTo,
    removePoints,
}: EditPointsProps): JSX.Element => {
    const containerRef = useRef<SVGGElement | null>(null);
    const ref = useRef<SVGRectElement>(null);

    const [selectedAnchorIndexes, setSelectedAnchorIndexes] = useState<number[]>([]);

    const { hasShapePointSelected } = useAnnotationScene();
    const { showContextMenu, hideContextMenu, contextConfig } = useAnnotatorContextMenu();
    const menuActionHandler = useRef(noop);

    useEventListener(KeyboardEvents.KeyDown, (event: KeyboardEvent) => {
        if (isKeyboardDelete(event as unknown as React.KeyboardEvent)) {
            event.preventDefault();

            handleRemovePoints();
        }
    });

    useEffect(() => {
        hasShapePointSelected.current = !isEmpty(selectedAnchorIndexes);

        if (menuActionHandler.current) {
            // Since `handleMenuAction` from contextMenu happens asynchronously, we must
            // guarantee that the value of `selectedAnchorIndexes` is the most up-to-date one.
            // So, for every `selectedAnchorIndexes` change, we update the handler function
            menuActionHandler.current = () => removePoints(selectedAnchorIndexes);
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedAnchorIndexes, hasShapePointSelected]);

    useEffect(() => {
        // Reset the selected anchors every time we add or remove a point
        setSelectedAnchorIndexes([]);
    }, [shape.points.length]);

    const handleRemovePoints = () => {
        removePoints(selectedAnchorIndexes);
        setSelectedAnchorIndexes([]);
    };

    const selectAnchorPoint = (idx: number, shiftKey: boolean, isContextMenu = false) => {
        setSelectedAnchorIndexes((indexes) => {
            if (isEmpty(indexes) || !shiftKey) {
                return [idx];
            }

            const isExistingIndex = indexes.includes(idx);

            // if shift key was pressed, toggle selection
            if (!isContextMenu && isExistingIndex) {
                return indexes.filter((otherIdx) => otherIdx !== idx);
            }

            if (isContextMenu && isExistingIndex) {
                return [...indexes];
            }

            return [...indexes, idx];
        });
    };

    useEventListener(
        MouseEvents.ContextMenu,
        (event) => {
            event.preventDefault();

            const { target, clientY, clientX } = event;
            const matcher = (element: HTMLElement) =>
                /^Resize polygon|Click to select point|Click to unselect/.test(
                    element.getAttribute('aria-label') ?? ''
                );

            if (matcher(target as HTMLElement)) {
                showContextMenu({
                    menuPosition: { top: clientY, left: clientX },
                    menuItems: [{ id: 'Delete point', children: [{ title: 'Delete', icon: <Delete /> }] }],
                    contextId: CONTEXT_ID,
                    ariaLabel: 'Delete point',
                    handleMenuAction: () => {
                        if (menuActionHandler.current) {
                            menuActionHandler.current();
                        }
                    },
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
            {/* Required to get correct relative mouse point */}
            <rect x={0} y={0} width={roi.width} height={roi.height} pointerEvents='none' fillOpacity={0} ref={ref} />

            <ResizeAnchorsGhostPoint
                svgRef={ref}
                moveAnchorTo={moveAnchorTo}
                shape={shape}
                addPoint={addPoint}
                onComplete={onComplete}
                zoom={zoom}
            />
            {shape.points.map((point, idx) => {
                const isSelected = selectedAnchorIndexes.includes(idx);
                const label = selectAnchorPointLabel(idx, isSelected, selectedAnchorIndexes);

                return (
                    <g
                        key={idx}
                        onClick={(event) => {
                            selectAnchorPoint(idx, event.shiftKey);
                        }}
                        aria-label={label}
                        aria-selected={isSelected}
                        onContextMenu={(event) => {
                            // we don't want event to be caught by annotation context menu
                            event.stopPropagation();
                            selectAnchorPoint(idx, event.shiftKey, true);
                        }}
                        fill={isSelected ? 'var(--energy-blue)' : undefined}
                    >
                        <ResizeAnchor
                            {...point}
                            zoom={zoom}
                            onComplete={onComplete}
                            label={`Resize polygon ${idx} anchor`}
                            moveAnchorTo={(x: number, y: number) => moveAnchorTo(idx, x, y)}
                        />
                    </g>
                );
            })}
        </g>
    );
};

interface ResizeAnchorsProps
    extends Pick<EditPointsProps, 'shape' | 'moveAnchorTo' | 'addPoint' | 'onComplete' | 'zoom'> {
    svgRef: RefObject<SVGRectElement>;
}

function ResizeAnchorsGhostPoint({ shape, addPoint, moveAnchorTo, zoom, onComplete, svgRef }: ResizeAnchorsProps) {
    const [ghostPoint, setGhostPoint] = useState<GhostPoint | undefined>(undefined);
    const ghostPointRef = useRef<GhostPoint | undefined>(undefined);

    const updateGhostPoint = (newGhost: GhostPoint | undefined) => {
        ghostPointRef.current = newGhost;
        setGhostPoint(newGhost);
    };

    const removeGhostPoint = () => {
        updateGhostPoint(undefined);
    };

    return (
        <>
            {shape.points.map((point, idx) => {
                const nextPoint = idx + 1 >= shape.points.length ? shape.points[0] : shape.points[idx + 1];

                const onPointerMove = (event: PointerEvent) => {
                    if (svgRef.current === null) {
                        return;
                    }

                    const mouse = getRelativePoint(svgRef.current, { x: event.clientX, y: event.clientY }, zoom);

                    const pointOnLine = projectPointOnLine([point, nextPoint], mouse);

                    if (pointOnLine !== undefined) {
                        const newGhostPoint = { idx: idx + 1, point: pointOnLine };
                        updateGhostPoint(newGhostPoint);
                    } else {
                        removeGhostPoint();
                    }
                };

                const onPointerDown = (event: PointerEvent) => {
                    const currentGhostPoint = ghostPointRef.current;
                    if (isLeftButton(event) && currentGhostPoint !== undefined) {
                        addPoint(currentGhostPoint.idx, currentGhostPoint.point.x, currentGhostPoint.point.y);
                    }
                };

                return (
                    <g onPointerLeave={removeGhostPoint} onPointerDown={onPointerDown} key={`${idx}`}>
                        <line
                            x1={point.x}
                            y1={point.y}
                            x2={nextPoint.x}
                            y2={nextPoint.y}
                            opacity={0}
                            stroke='black'
                            strokeWidth={`calc(${2 * ANCHOR_SIZE}px / var(--zoom-level))`}
                            onPointerMove={onPointerMove}
                            aria-label={`Line between point ${idx} and ${idx + 1}`}
                        />
                        {ghostPointRef.current === undefined ||
                        ghostPoint === undefined ||
                        ghostPoint.idx - 1 !== idx ? (
                            <></>
                        ) : (
                            <g>
                                <ResizeAnchor
                                    zoom={zoom}
                                    cursor='default'
                                    x={ghostPoint.point.x}
                                    y={ghostPoint.point.y}
                                    onComplete={onComplete}
                                    fill={'var(--energy-blue)'}
                                    label={`Add a point between point ${idx} and ${idx + 1}`}
                                    moveAnchorTo={(x: number, y: number) => {
                                        updateGhostPoint({ ...ghostPoint, point: { x, y } });
                                        moveAnchorTo(ghostPoint.idx, x, y);
                                    }}
                                />
                            </g>
                        )}
                    </g>
                );
            })}
        </>
    );
}
