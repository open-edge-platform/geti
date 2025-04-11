// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { DialogTrigger, Flex, Slider, Text, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';

import { PlaybackRate } from '../../../../../assets/icons';
import { ActionButton } from '../../../../../shared/components/button/button.component';
import { useStreamingVideoPlayer } from './streaming-video-player-provider.component';

interface PlaybackRate {
    value: number;
    label: string;
    key: number;
}

const AVAILABLE_PLAYBACK_RATES_MAPPING: Record<number, PlaybackRate> = {
    [1]: {
        value: 0.25,
        label: 'Slower',
        key: 1,
    },
    [2]: {
        value: 0.5,
        label: 'Slow',
        key: 2,
    },
    [3]: {
        value: 1,
        label: 'Normal',
        key: 3,
    },
};

const MIN_RATE = 1;
const MAX_RATE = 3;

export const PlaybackSpeedSlider = () => {
    const { playbackRate, setPlaybackRate } = useStreamingVideoPlayer();

    const selectedPlaybackRate =
        Object.values(AVAILABLE_PLAYBACK_RATES_MAPPING).find(({ value }) => value === playbackRate)?.key ?? MAX_RATE;

    return (
        <DialogTrigger type='popover'>
            <TooltipTrigger placement={'bottom'}>
                <ActionButton aria-label={'Open playback speed'}>
                    <View padding={'size-100'} width={'size-800'}>
                        <Flex alignItems={'center'} gap={'size-100'}>
                            <PlaybackRate />
                            <Text>{AVAILABLE_PLAYBACK_RATES_MAPPING[selectedPlaybackRate].value}x</Text>
                        </Flex>
                    </View>
                </ActionButton>
                <Tooltip>Playback speed</Tooltip>
            </TooltipTrigger>

            <View padding={'size-200'}>
                <Slider
                    id={'playback-speed'}
                    minValue={MIN_RATE}
                    maxValue={MAX_RATE}
                    step={1}
                    label={'Playback speed'}
                    getValueLabel={(value) => AVAILABLE_PLAYBACK_RATES_MAPPING[value].label}
                    aria-label={'Playback'}
                    value={selectedPlaybackRate}
                    onChange={(value) => {
                        setPlaybackRate(AVAILABLE_PLAYBACK_RATES_MAPPING[value].value);
                    }}
                    isFilled
                />
            </View>
        </DialogTrigger>
    );
};
