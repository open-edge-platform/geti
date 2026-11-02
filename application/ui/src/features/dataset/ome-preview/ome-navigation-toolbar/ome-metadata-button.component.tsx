// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { OmeImageInfo } from '@/api/types';
import { useTranslation } from '@/i18n';
import { ActionButton, DialogTrigger, Flex, Text, View } from '@geti-ui/ui';

type OmeMetadataButtonProps = {
    info: OmeImageInfo;
};

export const OmeMetadataButton = ({ info }: OmeMetadataButtonProps) => {
    const { t } = useTranslation();
    const rows: [string, string][] = [
        [
            t('annotator.ome.dimensions'),
            t('annotator.ome.dimensionsValue', {
                x: info.size_x,
                y: info.size_y,
                z: info.size_z,
                c: info.size_c,
                t: info.size_t,
            }),
        ],
        [t('annotator.ome.pixelType'), info.pixel_type],
        [t('annotator.ome.resolutionLevels'), String(Math.max(info.pyramid_levels.length, 1))],
        [t('annotator.ome.channels'), info.channels.map((channel) => channel.name ?? String(channel.index)).join(', ')],
    ];

    return (
        <DialogTrigger type={'popover'} placement={'top'}>
            <ActionButton isQuiet aria-label={'OME image metadata'}>
                <Text>{t('annotator.ome.metadata')}</Text>
            </ActionButton>
            <View padding={'size-200'}>
                <Flex direction={'column'} gap={'size-100'}>
                    {rows.map(([name, value]) => (
                        <Flex key={name} gap={'size-200'} justifyContent={'space-between'}>
                            <Text UNSAFE_style={{ fontWeight: 'bold' }}>{name}</Text>
                            <Text>{value}</Text>
                        </Flex>
                    ))}
                </Flex>
            </View>
        </DialogTrigger>
    );
};
