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

import { ComponentProps, MutableRefObject, ReactNode } from 'react';

import { ButtonGroup, Divider, Flex, Item, Menu, MenuTrigger, Text, View } from '@adobe/react-spectrum';
import { Popover } from '@react-spectrum/overlays';
import isEmpty from 'lodash/isEmpty';
import isFunction from 'lodash/isFunction';

import { ChevronLeft, Close, MoreMenu } from '../../../assets/icons';
import { FUX_NOTIFICATION_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../core/user-settings/hooks/use-global-settings.hook';
import { useDocsUrl } from '../../../hooks/use-docs-url/use-docs-url.hook';
import { useTutorialEnablement } from '../../hooks/use-tutorial-enablement.hook';
import { openNewTab } from '../../utils';
import { Button } from '../button/button.component';
import { CustomPopover } from '../custom-popover/custom-popover.component';
import { QuietActionButton } from '../quiet-button/quiet-action-button.component';
import { getFuxNotificationData, getStepInfo } from './utils';

import classes from './fux-notification.module.scss';

interface CustomPopoverProps extends Omit<ComponentProps<typeof Popover>, 'triggerRef' | 'children'> {
    settingsKey: FUX_NOTIFICATION_KEYS;
    children?: ReactNode;
    triggerRef: MutableRefObject<null>;
    onClose?: () => void;
}

export const FuxNotification = ({ settingsKey, triggerRef, state, onClose, children }: CustomPopoverProps) => {
    const settings = useUserGlobalSettings();
    const { close, isOpen, dismissAll, changeTutorial } = useTutorialEnablement(settingsKey);
    const { header, description, docUrl, nextStepId, previousStepId, showDismissAll, tipPosition } =
        getFuxNotificationData(settingsKey);
    const message = children ?? description;
    const url = useDocsUrl();
    const newDocUrl = `${url}${docUrl}`;

    if (!isOpen || isEmpty(message)) {
        return <></>;
    }

    if (!showDismissAll) {
        return (
            <CustomPopover
                ref={triggerRef}
                hideArrow={false}
                placement={tipPosition}
                state={state}
                UNSAFE_className={classes.container}
                isKeyboardDismissDisabled
            >
                <Flex direction={'row'} gap={'size-200'} alignItems={'center'}>
                    <Text order={1}>{message}</Text>

                    {docUrl && (
                        <Button
                            order={2}
                            variant='primary'
                            UNSAFE_style={{ border: 'none' }}
                            onPress={() => openNewTab(newDocUrl)}
                        >
                            Learn more
                        </Button>
                    )}

                    <Divider order={3} orientation='vertical' size='S' UNSAFE_className={classes.divider} />

                    <QuietActionButton
                        order={4}
                        onPress={() => {
                            state.close();
                            isFunction(onClose) && onClose();
                        }}
                        aria-label={'close first user experience notification'}
                        UNSAFE_className={classes.close}
                    >
                        <Close />
                    </QuietActionButton>
                </Flex>
            </CustomPopover>
        );
    }

    const onPressNext = () => {
        nextStepId && changeTutorial(settingsKey, nextStepId);
    };

    const onPressPrevious = () => {
        previousStepId && changeTutorial(settingsKey, previousStepId);
    };

    const stepInfo = getStepInfo(settingsKey);

    return (
        <CustomPopover
            ref={triggerRef}
            hideArrow={false}
            placement={tipPosition}
            state={state}
            UNSAFE_className={classes.container}
            isKeyboardDismissDisabled
        >
            <Flex direction={'row'} gap={'size-200'} alignItems={'center'}>
                <Flex UNSAFE_className={classes.fuxHeader}>
                    {header && <View UNSAFE_className={classes.header}>{header}</View>}
                    {stepInfo.stepNumber && stepInfo.totalCount && (
                        <Text UNSAFE_className={classes.steps}>
                            {stepInfo.stepNumber} of {stepInfo.totalCount}
                        </Text>
                    )}
                </Flex>

                <Text order={1}>{message}</Text>

                {docUrl && (
                    <Button
                        order={2}
                        variant='primary'
                        UNSAFE_style={{ border: 'none' }}
                        onPress={() => openNewTab(newDocUrl)}
                    >
                        Learn more
                    </Button>
                )}

                <Divider order={3} orientation='vertical' size='S' UNSAFE_className={classes.divider} />

                <ButtonGroup UNSAFE_className={classes.dialogButtonGroup}>
                    <Flex gap={'size-100'}>
                        {previousStepId && (
                            <Button
                                variant='primary'
                                aria-label='Back button'
                                id={`${settingsKey}-previous-button-id`}
                                onPress={onPressPrevious}
                                UNSAFE_className={classes.backButton}
                            >
                                <ChevronLeft />
                            </Button>
                        )}
                        {docUrl && (
                            <Button
                                variant='primary'
                                id={`${settingsKey}-learn-more-button-id`}
                                onPress={() => {
                                    openNewTab(newDocUrl);
                                }}
                            >
                                Learn more
                            </Button>
                        )}
                        {nextStepId ? (
                            <Button variant='primary' id='next-button-id' onPress={onPressNext}>
                                Next
                            </Button>
                        ) : (
                            <Button
                                variant='primary'
                                isPending={settings.isSavingConfig}
                                id='dismiss-button-id'
                                onPress={close}
                                aria-label='Dismiss help dialog'
                            >
                                Dismiss
                            </Button>
                        )}
                    </Flex>

                    <MenuTrigger>
                        <QuietActionButton
                            id={`${settingsKey}-more-btn-id`}
                            aria-label='Open to dismiss all help dialogs'
                            data-testid={`${settingsKey}-more-btn-id`}
                            UNSAFE_className={classes.moreMenu}
                        >
                            <MoreMenu />
                        </QuietActionButton>
                        <Menu id={`${settingsKey}-tutorial-card-menu-id`} onAction={dismissAll}>
                            <Item key={settingsKey} test-id={`${settingsKey}-dismiss-all-id`} textValue='Dismiss all'>
                                Dismiss all
                            </Item>
                        </Menu>
                    </MenuTrigger>
                </ButtonGroup>
            </Flex>
        </CustomPopover>
    );
};
