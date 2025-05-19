// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { Content, Dialog, DialogTrigger, Divider, Flex, Heading, Text, Tooltip, TooltipTrigger } from '@geti/ui';

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
