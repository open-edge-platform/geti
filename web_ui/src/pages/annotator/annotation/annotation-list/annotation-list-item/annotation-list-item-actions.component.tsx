// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@geti/ui';

import { Invisible } from '../../../../../assets/icons';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';
import { ToggleLockButton } from '../../toggle-lock-button/toggle-lock-button.component';
import { TOGGLE_VISIBILITY_COLOR_MODE } from '../../toggle-visibility-button/toggle-visibility-button.component';

interface AnnotationListItemActionsProps {
    isLocked: boolean;
    isHidden: boolean;
    isDisabled: boolean;
    textColor: string;
    annotationId: string;
    changeLock: (lock: boolean, annotationId: string) => void;
    showAnnotation: (annotationId: string) => void;
}

export const AnnotationListItemActions = ({
    isLocked,
    isHidden,
    isDisabled,
    textColor,
    annotationId,
    changeLock,
    showAnnotation,
}: AnnotationListItemActionsProps): JSX.Element => {
    const colorMode = isHidden ? TOGGLE_VISIBILITY_COLOR_MODE.ALWAYS_GRAYED_OUT : undefined;

    return (
        <Flex alignItems={'center'}>
            {isLocked && (
                <ToggleLockButton
                    id={annotationId}
                    onPress={() => changeLock(isLocked, annotationId)}
                    isLocked={isLocked}
                    isDisabled={isDisabled}
                    colorMode={colorMode}
                    aria-label='Unlock'
                />
            )}
            {isHidden && (
                <QuietActionButton
                    id={`annotation-list-item-${annotationId}-visibility-off`}
                    onPress={() => showAnnotation(annotationId)}
                    isDisabled={isDisabled}
                    aria-label='Show'
                >
                    <Invisible className={textColor} />
                </QuietActionButton>
            )}
        </Flex>
    );
};
