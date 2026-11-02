// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { OmeImageInfo } from '@/api/types';
import { useTranslation } from '@/i18n';
import { ActionButton, DialogTrigger, Text, Tooltip, TooltipTrigger } from '@geti-ui/ui';

import { OmeChannelsPanel } from './ome-channels-panel.component';

type OmeChannelsButtonProps = {
    mediaId: string;
    info: OmeImageInfo;
};

export const OmeChannelsButton = ({ mediaId, info }: OmeChannelsButtonProps) => {
    const { t } = useTranslation();

    return (
        <DialogTrigger type={'popover'} placement={'top'}>
            <TooltipTrigger placement={'bottom'}>
                <ActionButton isQuiet aria-label={'Channel display settings'}>
                    <Text>{t('annotator.ome.channels')}</Text>
                </ActionButton>
                <Tooltip>{t('annotator.ome.displayOnlyHint')}</Tooltip>
            </TooltipTrigger>
            <OmeChannelsPanel mediaId={mediaId} info={info} />
        </DialogTrigger>
    );
};
