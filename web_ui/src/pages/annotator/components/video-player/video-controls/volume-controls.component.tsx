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

import { Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { SoundOff, SoundOn } from '../../../../../assets/icons';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';

interface VolumeControlsProps {
    isMuted: boolean;
    setIsMuted: (isMuted: boolean) => void;
}

export const VolumeControls = ({ isMuted, setIsMuted }: VolumeControlsProps) => {
    return (
        <TooltipTrigger placement={'bottom'}>
            <QuietActionButton
                id='video-player-mute'
                onPress={() => setIsMuted(!isMuted)}
                aria-label={isMuted ? 'Unmute video' : 'Mute video'}
            >
                {isMuted ? <SoundOff /> : <SoundOn />}
            </QuietActionButton>
            <Tooltip>{isMuted ? 'Unmute video' : 'Mute video'}</Tooltip>
        </TooltipTrigger>
    );
};
