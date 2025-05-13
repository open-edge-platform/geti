// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ColorSwatch } from '@adobe/react-spectrum';
import { Checkbox } from '@geti/ui';
import { useFocusManager } from 'react-aria';

import { CloseSemiBold } from '../../../../assets/icons';
import { KeypointNode } from '../../../../core/annotations/shapes.interface';
import { useSetHoveredId } from '../../../../providers/hovered-provider/hovered-provider.component';
import { useSelected } from '../../../../providers/selected-provider/selected-provider.component';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { ListItemGrid } from '../list-item-grid.component';
import { ContentMenu } from './content-menu.component';
import { NodeLabel } from './node-label.component';

interface NodeContentProps {
    isLast: boolean;
    point: KeypointNode;
    onUpdate: (point: KeypointNode) => void;
}

export const NodeContent = ({ point, isLast, onUpdate }: NodeContentProps) => {
    const focusManager = useFocusManager();
    const { isActiveLearningMode } = useAnnotatorMode();
    const setHoveredPosePointLabelId = useSetHoveredId();
    const { addSelected, removeSelected, isSelected } = useSelected();

    const isPointSelected = isSelected(point.label.id);

    const handleFocus = () => {
        focusManager?.focusPrevious();
    };

    const handleCheckToggle = (isChecked: boolean) => {
        isChecked ? addSelected([point.label.id]) : removeSelected(point.label.id);
    };

    return (
        <ListItemGrid
            isLast={isLast}
            isSelected={isPointSelected}
            id={`keypoint-list-item-${point.label.id}`}
            ariaLabel={`Keypoint with id ${point.label.id}`}
            onHoverEnd={() => setHoveredPosePointLabelId(null)}
            onHoverStart={() => setHoveredPosePointLabelId(point.label.id)}
        >
            {isActiveLearningMode && (
                <ListItemGrid.Checkbox>
                    <Checkbox
                        isEmphasized
                        UNSAFE_style={{ padding: 0 }}
                        onFocus={handleFocus}
                        isSelected={isPointSelected}
                        onChange={handleCheckToggle}
                        id={`keypoint-list-checkbox-${point.label.id}`}
                        aria-label={`Select keypoint ${point.label.id}`}
                    />
                </ListItemGrid.Checkbox>
            )}

            <ListItemGrid.Color
                width={'size-150'}
                height={'size-150'}
                marginEnd={'size-150'}
                marginStart={isActiveLearningMode ? 'size-150' : 'size-0'}
            >
                {point.isVisible ? (
                    <ColorSwatch
                        width={'100%'}
                        height={'100%'}
                        aria-label={'label color'}
                        color={point.label.color}
                        UNSAFE_style={{ borderRadius: '50%', border: 'none' }}
                    />
                ) : (
                    <CloseSemiBold color={point.label.color} aria-label='occluded icon' />
                )}
            </ListItemGrid.Color>

            <ListItemGrid.Labels>
                <NodeLabel point={point} />
            </ListItemGrid.Labels>

            {isActiveLearningMode && (
                <ListItemGrid.ListMenu>
                    <ContentMenu point={point} onUpdate={onUpdate} />
                </ListItemGrid.ListMenu>
            )}
        </ListItemGrid>
    );
};
