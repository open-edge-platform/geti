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

import { Delete } from '../../../../../assets/icons';
import { KeypointNode, Point } from '../../../../../core/annotations/shapes.interface';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';
import { useSelected } from '../../../../annotator/providers/selected-provider/selected-provider.component';
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
                    <QuietActionButton
                        onPress={() => onDelete({ id, from, to })}
                        aria-label={`delete edge ${from.label.name} - ${to.label.name}`}
                    >
                        <Delete />
                    </QuietActionButton>
                }
            />
        );
    });
};
