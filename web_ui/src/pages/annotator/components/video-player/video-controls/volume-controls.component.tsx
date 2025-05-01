// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { QuietActionButton } from '@shared/components/quiet-button/quiet-action-button.component';

import { SoundOff, SoundOn } from '../../../../../assets/icons';

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
