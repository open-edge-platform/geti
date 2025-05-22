// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton } from '@geti/ui';
import { Delete } from '@geti/ui/icons';

import { KeypointNode, Point } from '../../../../../core/annotations/shapes.interface';
import { useSelected } from '../../../../../providers/selected-provider/selected-provider.component';
import { EdgeLine } from '../util';
import { Edge } from './edge.component';

interface PointEdgesProps {
    edges: Partial<EdgeLine>[];
    isDisabled: boolean;
    onDelete: (edge: EdgeLine) => void;
    onNewIntermediatePoint: (newPoint: Point, prevFrom: KeypointNode, prevTo: KeypointNode) => void;
}

export const PointEdges = ({ edges, isDisabled, onDelete, onNewIntermediatePoint }: PointEdgesProps) => {
    const { setSelected, removeSelected, isSelected } = useSelected();

    return edges.map(({ id, from, to }) => {
        if (id === undefined || from === undefined || to === undefined) {
            return null;
        }

        const isEdgeSelected = isSelected(id);

        return (
            <Edge
                key={`${from.label.id}-${to.label.id}`}
                id={id}
                to={to}
                from={from}
                isDisabled={isDisabled}
                isSelected={isEdgeSelected}
                onNewIntermediatePoint={onNewIntermediatePoint}
                onSelect={(selected) => {
                    selected ? removeSelected(id) : setSelected([id]);
                }}
                onRemoveSelected={removeSelected}
                onResetAndSelect={setSelected}
                contextMenu={
                    <ActionButton
                        isQuiet
                        onPress={() => onDelete({ id, from, to })}
                        aria-label={`delete edge ${from.label.name} - ${to.label.name}`}
                    >
                        <Delete />
                    </ActionButton>
                }
            />
        );
    });
};
