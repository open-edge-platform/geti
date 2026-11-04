// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import type { MediaOmePlane, OmeChannelSetting } from '@/api/types';
import {
    ActionButton,
    ColorSwatch,
    ColorSwatchPicker,
    Content,
    Dialog,
    DialogTrigger,
    Divider,
    Flex,
    Heading,
    RangeSlider,
    Slider,
    Switch,
    Text,
    type RangeValue,
} from '@geti-ui/ui';
import { uniq } from 'lodash-es';

import { getOmeDemoChannelNames, OME_DEMO_INTENSITY_MAX } from '../../../shared/ome-demo';
import { useSelectedMediaItem } from '../selected-media-item-provider.component';
import { Toolbar } from '../shell/toolbar-container/toolbar-container.component';

const CHANNEL_COLORS = ['#0000FF', '#00FF00', '#FF0000', '#00FFFF', '#FF00FF', '#FFFF00', '#FF8000', '#FFFFFF'];

type PlaneSliderProps = {
    label: string;
    index: number;
    size: number;
    onChange: (index: number) => void;
};

// Moves the thumb while dragging and loads the plane on release
const PlaneSlider = ({ label, index, size, onChange }: PlaneSliderProps) => {
    const [value, setValue] = useState(index);
    const [prevIndex, setPrevIndex] = useState(index);

    if (prevIndex !== index) {
        setPrevIndex(index);
        setValue(index);
    }

    return (
        <Slider
            label={label}
            minValue={0}
            maxValue={size - 1}
            value={value}
            onChange={setValue}
            onChangeEnd={onChange}
            getValueLabel={(current) => `${current + 1} / ${size}`}
            isFilled
            flex={1}
        />
    );
};

type ChannelProps = {
    name: string;
    setting: OmeChannelSetting;
    onChange: (setting: OmeChannelSetting) => void;
};

const Channel = ({ name, setting, onChange }: ChannelProps) => {
    const [range, setRange] = useState<RangeValue<number>>({ start: setting.window_min, end: setting.window_max });

    return (
        <Flex direction={'column'} gap={'size-50'}>
            <Flex alignItems={'center'} justifyContent={'space-between'}>
                <Switch isSelected={setting.enabled} onChange={(enabled) => onChange({ ...setting, enabled })}>
                    {name}
                </Switch>

                <DialogTrigger type={'popover'} hideArrow>
                    <ActionButton isQuiet aria-label={`Change color of ${name}`}>
                        <ColorSwatch color={setting.color} size={'S'} />
                    </ActionButton>
                    <Dialog aria-label={'Channel color'}>
                        <Content>
                            <ColorSwatchPicker
                                aria-label={`Color of ${name}`}
                                value={setting.color}
                                size={'S'}
                                onChange={(color) => onChange({ ...setting, color: color.toString('hex') })}
                            >
                                {uniq([setting.color.toUpperCase(), ...CHANNEL_COLORS]).map((color) => (
                                    <ColorSwatch key={color} color={color} />
                                ))}
                            </ColorSwatchPicker>
                        </Content>
                    </Dialog>
                </DialogTrigger>
            </Flex>

            <RangeSlider
                label={'Display range'}
                minValue={0}
                maxValue={OME_DEMO_INTENSITY_MAX}
                value={range}
                onChange={setRange}
                onChangeEnd={({ start, end }) =>
                    onChange({ ...setting, window_min: start, window_max: Math.max(end, start + 1) })
                }
                isDisabled={!setting.enabled}
                width={'100%'}
            />
        </Flex>
    );
};

const Channels = ({ plane }: { plane: MediaOmePlane }) => {
    const { setMediaItem } = useSelectedMediaItem();
    const names = getOmeDemoChannelNames(plane.id);

    const changeChannel = (setting: OmeChannelSetting) => {
        setMediaItem({
            ...plane,
            channels: plane.channels.map((channel) => (channel.channel === setting.channel ? setting : channel)),
        });
    };

    return (
        <DialogTrigger type={'popover'} placement={'top'}>
            <ActionButton isQuiet aria-label={'Channels'}>
                <Flex alignItems={'center'} gap={'size-75'} marginX={'size-100'}>
                    {plane.channels
                        .filter(({ enabled }) => enabled)
                        .map(({ channel, color }) => (
                            <ColorSwatch key={channel} color={color} size={'XS'} rounding={'full'} />
                        ))}
                    <Text>Channels</Text>
                </Flex>
            </ActionButton>

            <Dialog width={'size-4600'} aria-label={'Channels'}>
                <Heading>Channels</Heading>
                <Divider />
                <Content>
                    <Flex direction={'column'} gap={'size-200'}>
                        {plane.channels.map((setting) => (
                            <Channel
                                key={setting.channel}
                                name={names[setting.channel] ?? `Channel ${setting.channel}`}
                                setting={setting}
                                onChange={changeChannel}
                            />
                        ))}
                        <Text>Display only. Training uses a fixed channel mapping.</Text>
                    </Flex>
                </Content>
            </Dialog>
        </DialogTrigger>
    );
};

type OmeToolbarProps = {
    plane: MediaOmePlane;
    onSelectPlane: (plane: MediaOmePlane) => void;
};

export const OmeToolbar = ({ plane, onSelectPlane }: OmeToolbarProps) => {
    return (
        <Toolbar.Container>
            <Toolbar.Section>
                <Flex alignItems={'end'} gap={'size-300'} marginX={'size-100'}>
                    {plane.size_z > 1 && (
                        <PlaneSlider
                            label={'Z slice'}
                            index={plane.z_index}
                            size={plane.size_z}
                            onChange={(z_index) => onSelectPlane({ ...plane, z_index })}
                        />
                    )}
                    {plane.size_t > 1 && (
                        <PlaneSlider
                            label={'Time point'}
                            index={plane.t_index}
                            size={plane.size_t}
                            onChange={(t_index) => onSelectPlane({ ...plane, t_index })}
                        />
                    )}
                    <Channels plane={plane} />
                </Flex>
            </Toolbar.Section>
        </Toolbar.Container>
    );
};
