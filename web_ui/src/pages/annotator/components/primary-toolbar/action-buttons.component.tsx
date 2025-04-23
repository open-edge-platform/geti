// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { Flex } from '@react-spectrum/layout';
import isEmpty from 'lodash/isEmpty';

import { isKeypointTask } from '../../../../core/projects/utils';
import { Divider } from '../../../../shared/components/divider/divider.component';
import { FitImageToScreenButton } from '../../../../shared/components/fit-image-to-screen-button/fit-image-to-screen-button.component';
import { hasEqualId } from '../../../../shared/utils';
import {
    TOGGLE_VISIBILITY_COLOR_MODE,
    ToggleVisibilityButton,
} from '../../annotation/toggle-visibility-button/toggle-visibility-button.component';
import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { useIsSceneBusy } from '../../hooks/use-annotator-scene-interaction-state.hook';
import { getOutputFromTask } from '../../providers/task-chain-provider/utils';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { CanvasAdjustments } from './canvas-adjustments/canvas-adjustments.component';
import { HotKeysButton } from './hot-keys-button/hot-keys-button.component';

interface ActionButtonsProps {
    annotationToolContext: AnnotationToolContext;
}

export const ActionButtons = ({ annotationToolContext }: ActionButtonsProps): JSX.Element => {
    const isSceneBusy = useIsSceneBusy();
    const { tasks, selectedTask } = useTask();
    const { isActiveLearningMode } = useAnnotatorMode();
    const isKeypoint = Boolean(selectedTask && isKeypointTask(selectedTask));

    const {
        scene: { setHiddenAnnotations, annotations: annotationsScene },
    } = annotationToolContext;

    const annotations = getOutputFromTask(annotationsScene, tasks, selectedTask);
    const allAnnotationsHidden = useMemo(
        () => !isEmpty(annotations) && annotations.every((annotation) => annotation.isHidden),
        [annotations]
    );
    const toggleAnnotationsTooltip = allAnnotationsHidden ? 'Show annotations' : 'Hide annotations';
    const isToggleVisibilityButtonDisabled = isEmpty(annotations) || isSceneBusy || isKeypoint;

    const toggleVisibility = (isHidden: boolean) => {
        setHiddenAnnotations((annotation) => {
            if (annotations.some(hasEqualId(annotation.id))) {
                return isHidden;
            }

            return annotation.isHidden;
        });
    };

    const toggleVisibilityAnnotations = () => {
        toggleVisibility(!allAnnotationsHidden);
    };

    return (
        <Flex direction='column' gap='size-100' alignItems='center' justify-content='center'>
            <TooltipTrigger placement={'right'}>
                <FitImageToScreenButton key={'fit-image-to-screen-button'} />
                <Tooltip>Fit image to screen</Tooltip>
            </TooltipTrigger>

            {isActiveLearningMode && (
                <TooltipTrigger placement={'right'}>
                    <ToggleVisibilityButton
                        key={'all-annotations'}
                        id={'all-annotations'}
                        onPress={toggleVisibilityAnnotations}
                        isHidden={allAnnotationsHidden}
                        isDisabled={isToggleVisibilityButtonDisabled}
                        colorMode={TOGGLE_VISIBILITY_COLOR_MODE.NEVER_GRAYED_OUT}
                    />
                    <Tooltip>{toggleAnnotationsTooltip}</Tooltip>
                </TooltipTrigger>
            )}

            <CanvasAdjustments key={'canvas-adjustments'} />

            <Divider size={'S'} />
            <HotKeysButton />
        </Flex>
    );
};
