// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useRef } from 'react';

import { Heading, Text, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { CustomPopover } from '@shared/components/custom-popover/custom-popover.component';
import { Divider } from '@shared/components/divider/divider.component';
import { QuietActionButton } from '@shared/components/quiet-button/quiet-action-button.component';

import { Adjustments } from '../../../../assets/icons';
import { Screenshot } from '../../../camera-support/camera.interface';
import { DeviceSettings } from './device-settings.component';
import { SidebarThumbnail } from './sidebar-thumbnail.component';

import classes from './sidebar.module.scss';

interface CloseSidebarProps {
    screenshots: Screenshot[];
    isLivePrediction: boolean;
}

export const CloseSidebar = ({ screenshots, isLivePrediction }: CloseSidebarProps): JSX.Element => {
    const triggerRef = useRef(null);
    const settingsPopoverState = useOverlayTriggerState({});

    return (
        <View padding={'size-100'}>
            <SidebarThumbnail isCloseSidebar screenshots={screenshots} />

            {!isLivePrediction && (
                <>
                    <Divider size={'S'} marginTop={'size-250'} />
                    <Heading level={3} UNSAFE_className={classes.closeSidebarTitle}>
                        Images
                    </Heading>
                    <Text UNSAFE_className={classes.closeSidebarValue}>{screenshots.length}</Text>

                    <Divider size={'S'} marginTop={'size-250'} />
                    <Heading level={3} UNSAFE_className={classes.closeSidebarTitle}>
                        Videos
                    </Heading>
                    <Text UNSAFE_className={classes.closeSidebarValue}>13(12:10:22)</Text>
                </>
            )}

            <Divider size={'S'} marginTop={'size-250'} />

            <TooltipTrigger placement={'bottom'}>
                <QuietActionButton
                    ref={triggerRef}
                    marginX={'auto'}
                    marginTop={'size-150'}
                    UNSAFE_style={{ display: 'block' }}
                    onPress={settingsPopoverState.toggle}
                >
                    <Adjustments />
                </QuietActionButton>
                <Tooltip>Settings</Tooltip>
            </TooltipTrigger>

            <CustomPopover ref={triggerRef} state={settingsPopoverState} placement='left top'>
                <View padding='size-300'>
                    <DeviceSettings />
                </View>
            </CustomPopover>
        </View>
    );
};
