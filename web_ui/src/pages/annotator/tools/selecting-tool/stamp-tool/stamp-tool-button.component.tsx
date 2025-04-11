// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { AnimatePresence, motion } from 'framer-motion';
import { useHotkeys } from 'react-hotkeys-hook';

import { NoStamp, Stamp } from '../../../../../assets/icons';
import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { ANIMATION_PARAMETERS } from '../../../../../shared/animation-parameters/animation-parameters';
import { TooltipWithDisableButton } from '../../../../../shared/components/custom-tooltip/tooltip-with-disable-button';
import { QuietToggleButton } from '../../../../../shared/components/quiet-button/quiet-toggle-button.component';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { useAnnotatorHotkeys } from '../../../hooks/use-hotkeys-configuration.hook';
import { HOTKEY_OPTIONS } from '../../../hot-keys/utils';
import { useSelectingState } from '../selecting-state-provider.component';
import { SelectingToolType } from '../selecting-tool.enums';

interface StampToolButtonProps {
    isVisible: boolean;
    selectedAnnotations: Annotation[];
}

export const StampToolButton = ({ isVisible, selectedAnnotations }: StampToolButtonProps) => {
    const { hotkeys } = useAnnotatorHotkeys();
    const { activeTool, handleCreateStamp, handleCancelStamp } = useSelectingState();
    const isCreateStampBtnDisabled = selectedAnnotations.length > 1;
    const isStampToolSelected = activeTool === SelectingToolType.StampTool;
    const isStampToolActive = isStampToolSelected && !isCreateStampBtnDisabled;
    const ACTION_TEXT = isStampToolActive ? 'Cancel stamp' : 'Create stamp';

    const ACTIVE_BUTTON_TOOLTIP = isStampToolActive
        ? `${ACTION_TEXT}: ${hotkeys.close.slice(0, 3).toUpperCase()}`
        : `${ACTION_TEXT}: ${hotkeys['stamp-tool'].toUpperCase()}`;

    const BUTTON_ICON = isStampToolActive ? (
        <NoStamp data-testid={'cancel-stamp-icon-id'} />
    ) : (
        <Stamp data-testid={'create-stamp-icon-id'} />
    );

    const handleCreateStampCallback = (annotations: Annotation[]): void => {
        handleCreateStamp(annotations);
    };

    const handleStamp = (): void => {
        isStampToolActive ? handleCancelStamp() : handleCreateStampCallback(selectedAnnotations);
    };

    useHotkeys(
        hotkeys.close,
        () => {
            handleCancelStamp();
        },
        { ...HOTKEY_OPTIONS, enabled: isStampToolActive },
        [selectedAnnotations, isStampToolActive]
    );

    useHotkeys(
        hotkeys['stamp-tool'],
        () => {
            handleCreateStampCallback(selectedAnnotations);
        },
        { ...HOTKEY_OPTIONS, enabled: !isStampToolSelected && !isCreateStampBtnDisabled },
        [selectedAnnotations, isStampToolSelected, isCreateStampBtnDisabled]
    );

    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div variants={ANIMATION_PARAMETERS.FADE_ITEM} initial={'hidden'} animate={'visible'}>
                    <TooltipWithDisableButton
                        placement={'bottom'}
                        activeTooltip={ACTIVE_BUTTON_TOOLTIP}
                        disabledTooltip={'Stamp tool is disabled for multi-selection mode'}
                    >
                        <QuietToggleButton
                            aria-label={ACTION_TEXT}
                            isSelected={activeTool === SelectingToolType.StampTool}
                            id={`${idMatchingFormat(ACTION_TEXT)}-button-id`}
                            data-testid={`${idMatchingFormat(ACTION_TEXT)}-button-id`}
                            onPress={handleStamp}
                            isDisabled={isCreateStampBtnDisabled}
                        >
                            {BUTTON_ICON}
                        </QuietToggleButton>
                    </TooltipWithDisableButton>
                </motion.div>
            )}
        </AnimatePresence>
    );
};
