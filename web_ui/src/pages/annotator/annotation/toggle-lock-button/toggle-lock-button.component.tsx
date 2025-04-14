// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Lock, Unlock } from '../../../../assets/icons';
import { QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';
import { TOGGLE_VISIBILITY_COLOR_MODE } from '../toggle-visibility-button/toggle-visibility-button.component';

import classes from '../annotation-list/annotation-list-item/annotation-list-item.module.scss';

interface ToggleLockButtonProps {
    id: string;
    onPress: () => void;
    isLocked: boolean;
    isDisabled?: boolean;
    colorMode?: TOGGLE_VISIBILITY_COLOR_MODE;
}

export const ToggleLockButton = ({
    id,
    onPress,
    isLocked,
    isDisabled = false,
    colorMode = TOGGLE_VISIBILITY_COLOR_MODE.STANDARD,
}: ToggleLockButtonProps): JSX.Element => {
    const style = colorMode === TOGGLE_VISIBILITY_COLOR_MODE.ALWAYS_GRAYED_OUT ? classes.hiddenAnnotation : '';
    return (
        <QuietActionButton
            onPress={onPress}
            id={`annotation-${id}-toggle-lock`}
            data-testid={`annotation-${id}-toggle-lock`}
            aria-label={isLocked ? 'unlock annotation' : 'lock annotation'}
            isDisabled={isDisabled}
        >
            {isLocked ? (
                <Lock id={`annotation-${id}-lock-closed-icon`} className={style} />
            ) : (
                <Unlock id={`annotation-${id}-lock-open-icon`} className={style} />
            )}
        </QuietActionButton>
    );
};
