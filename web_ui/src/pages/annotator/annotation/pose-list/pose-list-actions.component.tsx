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

import { Flex, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';
import isEmpty from 'lodash/isEmpty';

import { CloseSemiBold, EyeSolid } from '../../../../assets/icons';
import { KeypointAnnotation } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { Checkbox } from '../../../../shared/components/checkbox/checkbox.component';
import { QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { useIsSceneBusy } from '../../hooks/use-annotator-scene-interaction-state.hook';
import { useAnnotationScene } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { useSelected } from '../../providers/selected-provider/selected-provider.component';
import { blurActiveInput } from '../../tools/utils';

interface PoseListActionsProps {
    keypointAnnotation: KeypointAnnotation;
}

export const OCCLUDE_TOOLTIP = 'Mark all as occluded';
export const VISIBLE_TOOLTIP = 'Mark all as visible';

export const DESELECT_TOOLTIP = 'Deselect all points';
export const SELECT_TOOLTIP = 'Select all points';

export const PoseListActions = ({ keypointAnnotation }: PoseListActionsProps) => {
    const isSceneBusy = useIsSceneBusy();
    const { updateAnnotation } = useAnnotationScene();
    const { isActiveLearningMode } = useAnnotatorMode();
    const { isSelected, addSelected, setSelected } = useSelected();

    const selectedPoints = keypointAnnotation.shape.points.filter(({ label }) => isSelected(label.id));
    const isEverythingVisible = selectedPoints.every(({ isVisible }) => isVisible);
    const hasSelectedPoints = !isEmpty(selectedPoints);

    const selectionTooltipText = hasSelectedPoints ? DESELECT_TOOLTIP : SELECT_TOOLTIP;
    const visibilityTooltipText = isEverythingVisible ? OCCLUDE_TOOLTIP : VISIBLE_TOOLTIP;
    const ToggleAllIcon = isEverythingVisible ? CloseSemiBold : EyeSolid;

    const selectAllPointsAriaLabel = `
    ${selectedPoints.length} out of ${keypointAnnotation.shape.points.length} points selected`;

    const handleSelectAllToggle = () => {
        if (hasSelectedPoints) {
            setSelected([]);
        } else {
            addSelected(keypointAnnotation.shape.points.map((point) => point.label.id));
        }
    };

    const handleSelectedVisibilityToggle = () => {
        updateAnnotation({
            ...keypointAnnotation,
            shape: {
                shapeType: ShapeType.Pose,
                points: keypointAnnotation.shape.points.map((point) =>
                    isSelected(point.label.id) ? { ...point, isVisible: !isEverythingVisible } : point
                ),
            },
        });
    };

    return (
        <Flex
            alignItems={'center'}
            justifyContent={'space-between'}
            UNSAFE_style={{ padding: dimensionValue('size-100') }}
        >
            <TooltipTrigger placement={'bottom'}>
                <Checkbox
                    isEmphasized
                    key='select-points'
                    id={'points-list-select-all'}
                    UNSAFE_style={{ padding: 0 }}
                    onFocusChange={blurActiveInput}
                    aria-label={selectAllPointsAriaLabel}
                    isSelected={hasSelectedPoints}
                    isDisabled={isSceneBusy || !isActiveLearningMode}
                    onChange={handleSelectAllToggle}
                />
                <Tooltip>{selectionTooltipText}</Tooltip>
            </TooltipTrigger>

            <TooltipTrigger placement={'bottom'}>
                <QuietActionButton
                    isDisabled={!hasSelectedPoints}
                    onPress={handleSelectedVisibilityToggle}
                    aria-label='visibility toggle'
                >
                    <ToggleAllIcon />
                </QuietActionButton>
                <Tooltip>{visibilityTooltipText}</Tooltip>
            </TooltipTrigger>
        </Flex>
    );
};
