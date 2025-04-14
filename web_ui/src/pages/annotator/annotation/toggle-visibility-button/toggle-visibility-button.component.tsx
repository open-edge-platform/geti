// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useHotkeys } from 'react-hotkeys-hook';

import { Invisible, Visible } from '../../../../assets/icons';
import { QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';
import { ANNOTATOR_MODE } from '../../core/annotation-tool-context.interface';
import { useAnnotatorHotkeys } from '../../hooks/use-hotkeys-configuration.hook';
import { HOTKEY_OPTIONS } from '../../hot-keys/utils';

import classes from './toggle-visibility-button.module.scss';

export enum TOGGLE_VISIBILITY_COLOR_MODE {
    ALWAYS_GRAYED_OUT,
    NEVER_GRAYED_OUT,
    STANDARD,
}

interface ToggleVisibilityButtonProps {
    id: string;
    onPress: () => void;
    isHidden: boolean;
    isDisabled?: boolean;
    colorMode?: TOGGLE_VISIBILITY_COLOR_MODE;
    mode?: ANNOTATOR_MODE;
}

export const ToggleVisibilityButton = ({
    id,
    onPress,
    isHidden,
    mode = ANNOTATOR_MODE.ACTIVE_LEARNING,
    isDisabled = false,
    colorMode = TOGGLE_VISIBILITY_COLOR_MODE.STANDARD,
}: ToggleVisibilityButtonProps): JSX.Element => {
    const { hotkeys } = useAnnotatorHotkeys();
    const ariaLabel = mode === ANNOTATOR_MODE.ACTIVE_LEARNING ? 'annotations' : 'predictions';

    useHotkeys(hotkeys.hideAllAnnotations, onPress, { ...HOTKEY_OPTIONS, enabled: !isDisabled }, [onPress]);

    return (
        <QuietActionButton
            onPress={onPress}
            aria-pressed={isHidden}
            isDisabled={isDisabled}
            id={`annotation-${id}-toggle-visibility`}
            data-testid={`annotation-${id}-toggle-visibility`}
            aria-label={isHidden ? `show ${ariaLabel}` : `hide ${ariaLabel}`}
        >
            {isHidden ? (
                <Invisible
                    id={`annotation-${id}-visibility-off-icon`}
                    className={colorMode === TOGGLE_VISIBILITY_COLOR_MODE.NEVER_GRAYED_OUT ? '' : classes.hiddenColor}
                />
            ) : (
                <Visible
                    id={`annotation-${id}-visibility-on-icon`}
                    className={colorMode === TOGGLE_VISIBILITY_COLOR_MODE.ALWAYS_GRAYED_OUT ? classes.hiddenColor : ''}
                />
            )}
        </QuietActionButton>
    );
};
