// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import type { OmeChannelDisplaySetting, OmeImageInfo } from '@/api/types';
import { useTranslation } from '@/i18n';
import { Button, Flex, Picker, PickerItem, RangeSlider, Switch, Text, View } from '@geti-ui/ui';
import { isEqual } from 'lodash-es';

import { useOmeChannelView, useUpdateOmeChannelView } from '../api/use-ome-image';
import { getDeclaredValueRange } from '../ome-render.utils';

type RgbTarget = OmeChannelDisplaySetting['target'];

const RGB_TARGETS: RgbTarget[] = ['red', 'green', 'blue'];

const hasDuplicateEnabledTarget = (settings: OmeChannelDisplaySetting[]): boolean => {
    const targets = settings.filter(({ enabled }) => enabled !== false).map(({ target }) => target);

    return new Set(targets).size !== targets.length;
};

// Keeps a local draft of the settings, reset whenever the server-side settings change
const useDraftSettings = (serverSettings: OmeChannelDisplaySetting[]) => {
    const [draft, setDraft] = useState(serverSettings);
    const [prevServerSettings, setPrevServerSettings] = useState(serverSettings);

    if (!isEqual(prevServerSettings, serverSettings)) {
        setPrevServerSettings(serverSettings);
        setDraft(serverSettings);
    }

    const updateSetting = (index: number, update: Partial<OmeChannelDisplaySetting>) => {
        setDraft((settings) => settings.map((setting, i) => (i === index ? { ...setting, ...update } : setting)));
    };

    return { draft, updateSetting, hasChanges: !isEqual(draft, serverSettings) };
};

type OmeChannelsPanelProps = {
    mediaId: string;
    info: OmeImageInfo;
    serverSettings: OmeChannelDisplaySetting[];
};

const OmeChannelsPanelContent = ({ mediaId, info, serverSettings }: OmeChannelsPanelProps) => {
    const { t } = useTranslation();
    const { draft, updateSetting, hasChanges } = useDraftSettings(serverSettings);
    const { updateChannelView, isPending } = useUpdateOmeChannelView(mediaId);
    const valueRange = getDeclaredValueRange(info, draft);
    const isInteger = info.pixel_type !== 'float' && info.pixel_type !== 'double';
    const targetLabels: Record<RgbTarget, string> = {
        red: t('annotator.ome.red'),
        green: t('annotator.ome.green'),
        blue: t('annotator.ome.blue'),
    };

    const channelName = (channel: number) =>
        info.channels[channel]?.name ?? t('annotator.ome.channelName', { index: channel });

    return (
        <Flex direction={'column'} gap={'size-200'} width={'size-4600'}>
            {draft.map((setting, index) => (
                <Flex key={`${setting.channel}-${index}`} direction={'column'} gap={'size-50'}>
                    <Flex alignItems={'center'} justifyContent={'space-between'} gap={'size-100'}>
                        <Switch
                            isEmphasized
                            isSelected={setting.enabled !== false}
                            onChange={(enabled) => updateSetting(index, { enabled })}
                        >
                            {channelName(setting.channel)}
                        </Switch>
                        <Picker
                            aria-label={'Channel color'}
                            width={'size-1600'}
                            selectedKey={setting.target}
                            onSelectionChange={(key) => updateSetting(index, { target: key as RgbTarget })}
                        >
                            {RGB_TARGETS.map((target) => (
                                <PickerItem key={target}>{targetLabels[target]}</PickerItem>
                            ))}
                        </Picker>
                    </Flex>
                    <RangeSlider
                        label={t('annotator.ome.displayRange')}
                        width={'100%'}
                        minValue={valueRange.min}
                        maxValue={valueRange.max}
                        step={isInteger ? 1 : (valueRange.max - valueRange.min) / 1000}
                        isDisabled={setting.enabled === false}
                        value={{ start: setting.window_min, end: setting.window_max }}
                        onChange={({ start, end }) =>
                            updateSetting(index, { window_min: start, window_max: Math.max(end, start + 1e-6) })
                        }
                    />
                </Flex>
            ))}

            <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-700)' }}>
                {t('annotator.ome.displayOnlyHint')}
            </Text>

            <Flex justifyContent={'end'}>
                <Button
                    variant={'accent'}
                    isPending={isPending}
                    isDisabled={!hasChanges || hasDuplicateEnabledTarget(draft)}
                    onPress={() => void updateChannelView(draft)}
                >
                    {t('common.actions.save')}
                </Button>
            </Flex>
        </Flex>
    );
};

export const OmeChannelsPanel = ({ mediaId, info }: Omit<OmeChannelsPanelProps, 'serverSettings'>) => {
    const { data: channelView } = useOmeChannelView(mediaId);

    if (channelView === undefined) {
        return null;
    }

    return (
        <View padding={'size-200'}>
            <OmeChannelsPanelContent mediaId={mediaId} info={info} serverSettings={channelView.settings} />
        </View>
    );
};
