// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, ColorMode, Flex, Provider, Tooltip, TooltipTrigger, View } from '@geti/ui';
import { InstallPWA } from '@geti/ui/icons';

import { AutoTrainingCreditsModalFactory } from '../../../../pages/annotator/notification/auto-training-credits-modal/auto-training-credits-modal.component';
import { ManualTrainingCreditDeductionNotificationFactory } from '../../../../pages/annotator/notification/manual-training-credit-deduction-notification/manual-training-credit-deduction-notification.component';
import { useProgressiveWebApp } from '../../../../providers/progressive-web-app-provider/progressive-web-app-provider.component';
import { useIsCreditAccountEnabled } from '../../../hooks/use-is-credit-account-enabled';
import { AutoTrainingCoachMark } from '../../coach-mark/fux-notifications/auto-training-coach-mark.component';
import { ActiveLearningConfiguration } from '../active-learning-configuration/active-learning-configuration.component';
import { CreditBalanceStatus } from '../credit-balance/credit-balance-status.component';
import { JobsActionIcon } from '../jobs-management/jobs-action-icon.component';
import { HelpActions } from './help-actions/help-actions.component';
import { UserActions } from './user-actions/user-actions.component';

import classes from './header-actions.module.scss';

interface HeaderMenuProps {
    isProject: boolean;
    isDarkMode: boolean;
    isAnomalyProject?: boolean;
}

export const HeaderActions = ({ isDarkMode, isProject, isAnomalyProject }: HeaderMenuProps): JSX.Element => {
    const isCreditAccountEnabled = useIsCreditAccountEnabled();
    const { isPWAReady, handlePromptInstallApp } = useProgressiveWebApp();

    const isAutoTrainingAvailable = isProject && !isAnomalyProject;

    return (
        <View marginEnd='size-400'>
            <Provider isQuiet>
                <Flex
                    gap='size-75'
                    id='header-actions-container'
                    UNSAFE_className={isDarkMode ? '' : classes.basicColor}
                >
                    {isPWAReady && (
                        <TooltipTrigger placement={'bottom'}>
                            <ActionButton
                                isQuiet
                                key='install-app'
                                id='install-app'
                                colorMode={isDarkMode ? ColorMode.DARK : ColorMode.LIGHT}
                                aria-label='Install Geti (PWA)'
                                onPress={handlePromptInstallApp}
                            >
                                <InstallPWA />
                            </ActionButton>
                            <Tooltip>Install Geti (PWA)</Tooltip>
                        </TooltipTrigger>
                    )}

                    {isAutoTrainingAvailable && (
                        <ActiveLearningConfiguration selectedTask={null} isDarkMode={isDarkMode} />
                    )}

                    {isCreditAccountEnabled && (
                        <CreditBalanceStatus key='credit-balance-status' isDarkMode={isDarkMode} />
                    )}

                    <View key='jobs-management'>
                        <JobsActionIcon isDarkMode={isDarkMode} />
                        {isProject && <AutoTrainingCoachMark styles={{ right: '84px' }} />}
                    </View>

                    <TooltipTrigger placement={'bottom'}>
                        <HelpActions key='docs-actions' isDarkMode={isDarkMode} />
                        <Tooltip>Help</Tooltip>
                    </TooltipTrigger>

                    <TooltipTrigger placement={'bottom'}>
                        <UserActions key='user-actions' isDarkMode={isDarkMode} />
                        <Tooltip>User</Tooltip>
                    </TooltipTrigger>
                </Flex>

                <AutoTrainingCreditsModalFactory />

                <ManualTrainingCreditDeductionNotificationFactory />
            </Provider>
        </View>
    );
};
