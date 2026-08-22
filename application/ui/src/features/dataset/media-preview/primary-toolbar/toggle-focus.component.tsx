// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ActionButton, Tooltip, TooltipTrigger } from '@geti-ui/ui';
import { LabelGroup } from '@geti-ui/ui/icons';
import { useTranslation } from 'react-i18next';

import { IconWrapper } from '../../../../components/icon-wrapper/icon-wrapper.component';
import { useAnnotationVisibility } from '../../../../shared/annotator/annotation-visibility-provider.component';

export const ToggleFocus = () => {
    const { t } = useTranslation();

    const { toggleFocus, isFocussed } = useAnnotationVisibility();

    return (
        <TooltipTrigger>
            <ActionButton isQuiet onPress={toggleFocus} aria-label={t('annotator.toggleFocus')}>
                <IconWrapper isSelected={isFocussed}>
                    <LabelGroup />
                </IconWrapper>
            </ActionButton>
            <Tooltip>{t('annotator.toggleFocus')}</Tooltip>
        </TooltipTrigger>
    );
};
