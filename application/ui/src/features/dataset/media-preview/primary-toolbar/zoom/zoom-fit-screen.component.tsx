// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ActionButton, Tooltip, TooltipTrigger } from '@geti-ui/ui';
import { FitScreen } from '@geti-ui/ui/icons';
import { useHotkeys } from 'react-hotkeys-hook';
import { useTranslation } from 'react-i18next';

import { IconWrapper } from '../../../../../components/icon-wrapper/icon-wrapper.component';
import { useSetZoom } from '../../../../../components/zoom/zoom.provider';
import { HOTKEYS } from '../../../../../shared/hotkeys-definition';

export const ZoomFitScreen = () => {
    const { t } = useTranslation();

    const { fitToScreen } = useSetZoom();

    useHotkeys(HOTKEYS.fitToScreen, fitToScreen, [fitToScreen]);

    return (
        <TooltipTrigger>
            <ActionButton isQuiet onPress={fitToScreen} aria-label={t('annotator.fitToScreen')}>
                <IconWrapper>
                    <FitScreen />
                </IconWrapper>
            </ActionButton>
            <Tooltip>{t('annotator.fitToScreen')}</Tooltip>
        </TooltipTrigger>
    );
};
