// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useState } from 'react';

import {
    Content,
    Dialog,
    DialogTrigger,
    Divider,
    Flex,
    Heading,
    Text,
    Tooltip,
    TooltipTrigger,
} from '@adobe/react-spectrum';

import { Adjustments, Close } from '../../../../../assets/icons';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';
import { useAnnotatorCanvasSettings } from '../../../providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component';
import { AdjustmentsList } from './adjustments-list.component';

import classes from './canvas-adjustments.module.scss';

export const CanvasAdjustments = (): JSX.Element => {
    const [isTooltipDisabled, setIsTooltipDisabled] = useState(false);
    const { canvasSettingsState, handleSaveConfig } = useAnnotatorCanvasSettings();

    return (
        <TooltipTrigger placement={'right'} isDisabled={isTooltipDisabled}>
            <DialogTrigger
                type={'popover'}
                placement={'right'}
                hideArrow
                onOpenChange={(isOpen) => {
                    setIsTooltipDisabled(isOpen);
                    // save on close event, i.e. isOpen === false
                    !isOpen && handleSaveConfig();
                }}
            >
                <QuietActionButton aria-label={'Canvas adjustments'}>
                    <Adjustments />
                </QuietActionButton>
                {(close): JSX.Element => (
                    <Dialog height={'36rem'} width={'32rem'} UNSAFE_className={classes.canvasDialog}>
                        <Heading>
                            <Flex justifyContent={'space-between'} alignItems={'center'}>
                                <Text>Adjustments</Text>
                                <QuietActionButton onPress={close} aria-label={'Close canvas adjustments'}>
                                    <Close />
                                </QuietActionButton>
                            </Flex>
                        </Heading>
                        <Divider marginY={'size-150'} UNSAFE_className={classes.canvasAdjustmentsDivider} />
                        <Content>
                            <AdjustmentsList canvasSettingsConfig={canvasSettingsState} />
                        </Content>
                    </Dialog>
                )}
            </DialogTrigger>
            <Tooltip>Change canvas settings</Tooltip>
        </TooltipTrigger>
    );
};
