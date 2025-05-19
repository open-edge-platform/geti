// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Checkbox, dimensionValue, Flex, Tooltip, TooltipTrigger } from '@geti/ui';
import { isEmpty } from 'lodash-es';

import { CloseSemiBold, EyeSolid } from '../../../../assets/icons';
import { KeypointAnnotation } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { useSelected } from '../../../../providers/selected-provider/selected-provider.component';
import { QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { useIsSceneBusy } from '../../hooks/use-annotator-scene-interaction-state.hook';
import { useAnnotationScene } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
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
