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

import { useRef } from 'react';

import { Heading, Text, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';
import { useOverlayTriggerState } from '@react-stately/overlays';

import { Adjustments } from '../../../../assets/icons';
import { CustomPopover } from '../../../../shared/components/custom-popover/custom-popover.component';
import { Divider } from '../../../../shared/components/divider/divider.component';
import { QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';
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
