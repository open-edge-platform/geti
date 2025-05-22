// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, Tooltip, TooltipTrigger } from '@geti/ui';
import { SoundOff, SoundOn } from '@geti/ui/icons';

interface VolumeControlsProps {
    isMuted: boolean;
    setIsMuted: (isMuted: boolean) => void;
}

export const VolumeControls = ({ isMuted, setIsMuted }: VolumeControlsProps) => {
    return (
        <TooltipTrigger placement={'bottom'}>
            <ActionButton
                isQuiet
                id='video-player-mute'
                onPress={() => setIsMuted(!isMuted)}
                aria-label={isMuted ? 'Unmute video' : 'Mute video'}
            >
                {isMuted ? <SoundOff /> : <SoundOn />}
            </ActionButton>
            <Tooltip>{isMuted ? 'Unmute video' : 'Mute video'}</Tooltip>
        </TooltipTrigger>
    );
};
