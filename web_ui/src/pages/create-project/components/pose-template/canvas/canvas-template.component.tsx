// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import isEqual from 'lodash/isEqual';
import isNil from 'lodash/isNil';
import { v4 as uuidv4 } from 'uuid';

import { Delete, SortUpDown } from '../../../../../assets/icons';
import { RegionOfInterest } from '../../../../../core/annotations/annotation.interface';
import { KeypointNode, Point } from '../../../../../core/annotations/shapes.interface';
import { useIsPressed } from '../../../../../hooks/use-is-pressed/use-is-pressed.hook';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';
import { KeyMap } from '../../../../../shared/keyboard-events/keyboard.interface';
import { getIds, hasDifferentId } from '../../../../../shared/utils';
import { useSelected } from '../../../../annotator/providers/selected-provider/selected-provider.component';
import { ClosestKeypoint } from '../../../../annotator/tools/edit-tool/edit-keypoint/closest-keypoint.component';
import { useZoom } from '../../../../annotator/zoom/zoom-provider.component';
import { getPointInRoi } from '../../../../utils';
import {
    EdgeLine,
    getDefaultLabelStructure,
    isDifferentLabel,
    isEdgeConnectingPoints,
    isEqualLabel,
    isNotMatchingEdge,
    TemplateState,
    TemplateStateWithHistory,
    updateWithLatestPoints,
} from '../util';
import { DrawingBox } from './drawing-box.component';
import { ExpandablePointLabel } from './expandable-point-label.component';
import { GhostLineEdge } from './ghost-line-edge.component';
import { PointEdges } from './point-edges.component';
import { Points } from './points.component';

export interface CanvasTemplateProps {
    roi: RegionOfInterest;
    state: TemplateState;
    isAddPointEnabled?: boolean;
    isLabelOptionsEnabled?: boolean;
    onStateUpdate: (templateState: TemplateStateWithHistory) => void;
}

const isStandAloneShiftKey = (event: KeyboardEvent) => {
    return event.key === KeyMap.Shift && event.ctrlKey === false && event.altKey === false && event.metaKey === false;
};

export const CanvasTemplate = ({
    roi,
    state: { edges, points },
    isAddPointEnabled = true,
    isLabelOptionsEnabled = true,
    onStateUpdate,
}: CanvasTemplateProps) => {
    const { zoomState } = useZoom();
    const { setSelected, isSelected } = useSelected();
    const [visibleLabelId, setVisibleLabelId] = useState<null | string>(null);

    const [ghostLine, setGhostLine] = useState<{ from: KeypointNode; to?: Point } | null>(null);

    const isDrawingGhostLine = !isNil(ghostLine?.from);
    const selectedPoint = points.find(({ label }) => isSelected(label.id));

    const isShiftPress = useIsPressed({
        key: KeyMap.Shift,
        predicated: isStandAloneShiftKey,
        onKeyDown: () => {
            selectedPoint && setGhostLine({ from: selectedPoint });
        },
        onKeyUp: () => {
            setGhostLine(null);
        },
    });

    const handleNewPoint = (newPoint: KeypointNode) => {
        const newEdges = ghostLine !== null ? [...edges, { ...ghostLine, to: newPoint, id: uuidv4() }] : edges;

        setSelected([newPoint.label.id]);
        setGhostLine(isShiftPress ? { from: newPoint } : null);
        onStateUpdate({ points: [...points, newPoint], edges: newEdges, skipHistory: false });
        handleSelectConnectedEdges(newPoint, newEdges);
    };

    const handleNewIntermediatePoint = (rawPoint: Point, prevFrom: KeypointNode, prevTo: KeypointNode) => {
        const newPoint = {
            label: getDefaultLabelStructure(String(points.length + 1)),
            isVisible: true,
            ...rawPoint,
        };

        const filteredEdges = edges.filter(isNotMatchingEdge(prevFrom, prevTo));

        const newEdges = [
            ...filteredEdges,
            { from: prevTo, to: newPoint, id: uuidv4() },
            { from: prevFrom, to: newPoint, id: uuidv4() },
        ];

        setSelected([newPoint.label.id]);
        setGhostLine(null);
        onStateUpdate({ points: [...points, newPoint], edges: newEdges, skipHistory: false });
        handleSelectConnectedEdges(newPoint, newEdges);
    };

    const handlePointMove = (point: KeypointNode, index: number, skipHistory = true) => {
        const newPoints = points.with(index, getPointInRoi(point, roi));
        onStateUpdate({ edges, points: newPoints, skipHistory });
    };

    const handleDeletePoint = (point: KeypointNode) => {
        onStateUpdate({
            points: points.filter(isDifferentLabel(point)),
            edges: edges.filter((currentEdge) => {
                return isDifferentLabel(currentEdge.from)(point) && isDifferentLabel(currentEdge.to)(point);
            }),
        });
    };

    const handleGhostLine = (point: KeypointNode) => {
        const isGhostLineInitialPoint = isEqual(ghostLine?.from, point);

        if (isGhostLineInitialPoint) {
            setGhostLine(null);
        }

        if (ghostLine && !isGhostLineInitialPoint) {
            const isNewEdge = edges.some(isEdgeConnectingPoints(ghostLine.from, point)) === false;

            setGhostLine(null);

            const newEdges = isNewEdge ? [...edges, { ...ghostLine, to: point, id: uuidv4() }] : edges;
            onStateUpdate({ points, edges: newEdges });
        }
    };

    const handleGhostLineEndMoving = ({ x, y }: Point) => {
        if (!isDrawingGhostLine) {
            return;
        }

        setGhostLine({ from: ghostLine.from, to: { x, y } });
    };

    const handleDeleteEdge = (edgeLine: EdgeLine) => {
        onStateUpdate({ points, edges: edges.filter(hasDifferentId(edgeLine.id)) });
    };

    const handleSelectConnectedEdges = (point: KeypointNode, newEdges: EdgeLine[]) => {
        const connectedLines = newEdges.filter(({ from, to }) => {
            return from?.label.id === point.label.id || to?.label.id === point.label.id;
        });

        setSelected([point.label.id, ...getIds(connectedLines)]);
    };

    return (
        <>
            <ClosestKeypoint
                // eslint-disable-next-line jsx-a11y/aria-role
                role={'editor'}
                width={'100%'}
                height={'100%'}
                nodes={points}
                onClosestElement={({ label }) => setVisibleLabelId(label.id)}
                style={{
                    boxSizing: 'border-box',
                    border: '1px solid var(--spectrum-global-color-gray-200)',
                }}
            >
                {isAddPointEnabled && (
                    <DrawingBox
                        totalPoints={points.length + 1}
                        onAddPoint={handleNewPoint}
                        onPointerMove={handleGhostLineEndMoving}
                    />
                )}

                {!isNil(ghostLine?.to) && <GhostLineEdge from={ghostLine.from} to={ghostLine.to} />}

                <PointEdges
                    edges={edges.map(updateWithLatestPoints(points))}
                    onDelete={handleDeleteEdge}
                    isDisabled={isDrawingGhostLine || !isAddPointEnabled}
                    onNewIntermediatePoint={handleNewIntermediatePoint}
                />

                <Points
                    points={points}
                    zoom={zoomState.zoom}
                    cursor={isDrawingGhostLine ? 'pointer' : 'move'}
                    onStart={(point) => {
                        handleGhostLine(point);
                        setSelected([point.label.id]);
                        handleSelectConnectedEdges(point, edges);
                        isShiftPress && setGhostLine({ from: point });
                    }}
                    onMove={handlePointMove}
                    onComplete={(point, index) => {
                        handlePointMove(point, index, false);
                        handleSelectConnectedEdges(point, edges);
                    }}
                />
            </ClosestKeypoint>

            <div aria-label='label container' style={{ position: 'absolute', top: 0, left: 0 }}>
                {points.map((point) => {
                    return (
                        <ExpandablePointLabel
                            key={point.label.id}
                            point={point}
                            isOptionsEnabled={isLabelOptionsEnabled}
                            isVisible={visibleLabelId === point.label.id}
                            isFaded={isDrawingGhostLine && selectedPoint?.label.id !== point.label.id}
                        >
                            <QuietActionButton
                                aria-label={`link keypoint ${point.label.name}`}
                                onPress={() => {
                                    setSelected([point.label.id]);
                                    setGhostLine({ from: point });
                                    handleGhostLine(point);
                                }}
                            >
                                <SortUpDown />
                            </QuietActionButton>
                            <QuietActionButton
                                onPress={() => handleDeletePoint(point)}
                                isDisabled={ghostLine?.from && isEqualLabel(ghostLine.from)(point)}
                                aria-label={`delete keypoint ${point.label.name}`}
                            >
                                <Delete />
                            </QuietActionButton>
                        </ExpandablePointLabel>
                    );
                })}
            </div>
        </>
    );
};
