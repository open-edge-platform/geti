// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ActionButton, Flex, Tooltip, TooltipTrigger } from '@geti-ui/ui';
import { Add, Remove } from '@geti-ui/ui/icons';
import { useTranslation } from 'react-i18next';

import { IconWrapper } from '../../../../../components/icon-wrapper/icon-wrapper.component';
import { useSetZoom, useZoom } from '../../../../../components/zoom/zoom.provider';

export const ZoomSelector = () => {
    const { t } = useTranslation();

    const zoom = useZoom();
    const { onZoomChange } = useSetZoom();

    return (
        <>
            <TooltipTrigger>
                <ActionButton
                    isQuiet
                    aria-label={t('annotator.zoomIn')}
                    onPress={() => onZoomChange(1)}
                    isDisabled={zoom.scale >= zoom.maxZoomIn}
                >
                    <IconWrapper>
                        <Add />
                    </IconWrapper>
                </ActionButton>
                <Tooltip>{t('annotator.zoomIn')}</Tooltip>
            </TooltipTrigger>

            <Flex justifyContent={'end'} width={'size-350'}>
                <span
                    aria-label={t('annotator.zoomLevel')}
                    data-value={zoom.scale}
                    style={{ fontSize: 'var(--spectrum-global-dimension-font-size-50)' }}
                >
                    {(zoom.scale * 100).toFixed(0)}%
                </span>
            </Flex>

            <TooltipTrigger>
                <ActionButton
                    isQuiet
                    aria-label={t('annotator.zoomOut')}
                    onPress={() => onZoomChange(-1)}
                    isDisabled={zoom.scale <= zoom.initialCoordinates.scale}
                >
                    <IconWrapper>
                        <Remove />
                    </IconWrapper>
                </ActionButton>
                <Tooltip>{t('annotator.zoomOut')}</Tooltip>
            </TooltipTrigger>
        </>
    );
};
