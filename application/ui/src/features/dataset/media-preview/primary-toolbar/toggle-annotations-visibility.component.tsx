// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ActionButton, Tooltip, TooltipTrigger } from '@geti-ui/ui';
import { Invisible, Visible } from '@geti-ui/ui/icons';
import { useHotkeys } from 'react-hotkeys-hook';
import { useTranslation } from 'react-i18next';

import { useAnnotationVisibility } from '../../../../shared/annotator/annotation-visibility-provider.component';
import { HOTKEYS } from '../../../../shared/hotkeys-definition';

export const ToggleAnnotationsVisibility = () => {
    const { t } = useTranslation();

    const { isVisible, toggleVisibility } = useAnnotationVisibility();

    useHotkeys(HOTKEYS.toggleAnnotationsVisibility, toggleVisibility, [toggleVisibility]);

    return (
        <TooltipTrigger placement={'right'}>
            <ActionButton
                aria-label={isVisible ? t('annotator.hideAnnotations') : t('annotator.showAnnotations')}
                isQuiet
                onPress={toggleVisibility}
            >
                {isVisible ? <Visible /> : <Invisible />}
            </ActionButton>
            <Tooltip>{isVisible ? t('annotator.hideAnnotations') : t('annotator.showAnnotations')}</Tooltip>
        </TooltipTrigger>
    );
};
