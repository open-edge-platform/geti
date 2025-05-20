// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

import { Button, ButtonGroup, Divider, Flex, Item, Menu, MenuTrigger, Text, View } from '@geti/ui';
import { isEmpty } from 'lodash-es';

import { ChevronLeft, Close, MoreMenu } from '../../../assets/icons';
import { FUX_NOTIFICATION_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../core/user-settings/hooks/use-global-settings.hook';
import { useDocsUrl } from '../../../hooks/use-docs-url/use-docs-url.hook';
import { useTutorialEnablement } from '../../hooks/use-tutorial-enablement.hook';
import { QuietActionButton } from '../quiet-button/quiet-action-button.component';
import { onPressLearnMore } from '../tutorials/utils';
import { getFuxNotificationData, getStepInfo } from './utils';

import classes from './coach-mark.module.scss';

interface CoachMarkProps {
    settingsKey: FUX_NOTIFICATION_KEYS;
    styles?: CSSProperties;
    customDescription?: string;
}

export const CoachMark = ({ settingsKey, styles, customDescription = '' }: CoachMarkProps): JSX.Element => {
    const settings = useUserGlobalSettings();
    const { close, isOpen, dismissAll, changeTutorial } = useTutorialEnablement(settingsKey);
    const { header, description, docUrl, nextStepId, previousStepId, showDismissAll, tipPosition } =
        getFuxNotificationData(settingsKey);
    const message = customDescription ? customDescription : description;
    const url = useDocsUrl();
    const newDocUrl = `${url}${docUrl}`;

    if (!isOpen || isEmpty(message)) {
        return <></>;
    }

    if (!showDismissAll) {
        return (
            <View
                UNSAFE_className={[classes.dialogWrapper, tipPosition ? classes[tipPosition] : ''].join(' ')}
                UNSAFE_style={styles}
            >
                <Text UNSAFE_className={classes.dialogDescription}>{message}</Text>
                {docUrl && (
                    <Button
                        variant='primary'
                        id={`${settingsKey}-learn-more-button-id`}
                        onPress={() => {
                            onPressLearnMore(newDocUrl);
                        }}
                        marginStart={'size-300'}
                        UNSAFE_style={{ border: 'none' }}
                    >
                        Learn more
                    </Button>
                )}
                <Divider orientation='vertical' size='S' UNSAFE_className={classes.coachMarkDivider} />
                <QuietActionButton onPress={close} aria-label={'Dismiss help dialog'} UNSAFE_className={classes.close}>
                    <Close />
                </QuietActionButton>
            </View>
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
        <View
            UNSAFE_className={[classes.dialogWrapper, tipPosition ? classes[tipPosition] : ''].join(' ')}
            UNSAFE_style={styles}
        >
            <Flex UNSAFE_className={classes.coachMarkHeader}>
                {header && <View UNSAFE_className={classes.header}>{header}</View>}
                {stepInfo.stepNumber && stepInfo.totalCount && (
                    <Text UNSAFE_className={classes.steps}>
                        {stepInfo.stepNumber} of {stepInfo.totalCount}
                    </Text>
                )}
            </Flex>

            <Text UNSAFE_className={classes.dialogDescription}>{message}</Text>

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
                                onPressLearnMore(newDocUrl);
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
        </View>
    );
};
