// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { forwardRef, useEffect, useRef } from 'react';

import { Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { FocusableRef } from '@react-types/shared';
import { isNil } from 'lodash-es';
import { useParams } from 'react-router-dom';
import { useOverlayTriggerState } from 'react-stately';

import { CreditCard } from '../../../../assets/icons';
import { useCreditsQueries } from '../../../../core/credits/hooks/use-credits-api.hook';
import { paths } from '../../../../core/services/routes';
import { FUX_NOTIFICATION_KEYS, FUX_SETTINGS_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../../core/user-settings/hooks/use-global-settings.hook';
import { getSettingsOfType } from '../../../../core/user-settings/utils';
import { useUsers } from '../../../../core/users/hook/use-users.hook';
import { useOrganizationIdentifier } from '../../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { usePrevious } from '../../../../hooks/use-previous/use-previous.hook';
import { useProject } from '../../../../pages/project-details/providers/project-provider/project-provider.component';
import { ONE_MINUTE } from '../../../utils';
import { ColorMode, QuietActionButton } from '../../quiet-button/quiet-action-button.component';
import { CreditsToConsume } from './credits-to-consume.component';
import { FuxNotification } from './fux-notification/fux-notification.component';
import { isBalanceLow } from './util';

import classes from './credit-balance.module.scss';

interface CreditBalanceButtonProps {
    isDarkMode: boolean;
    onPress?: () => void;
    UNSAFE_className?: string;
}

export const CreditBalanceButton = ({ isDarkMode }: { isDarkMode: boolean }) => {
    const params = useParams<{ projectId: string }>();

    if (isNil(params.projectId)) {
        return <CreditBalanceButtonDefault isDarkMode={isDarkMode} />;
    }

    return <CreditBalanceButtonFuxNotification isDarkMode={isDarkMode} />;
};

const CreditBalanceButtonDefault = forwardRef(
    ({ onPress, isDarkMode, UNSAFE_className }: CreditBalanceButtonProps, ref: FocusableRef<HTMLButtonElement>) => {
        const { useGetOrganizationBalanceQuery } = useCreditsQueries();
        const { organizationId } = useOrganizationIdentifier();
        const { data: organizationBalance } = useGetOrganizationBalanceQuery(
            { organizationId },
            { refetchInterval: ONE_MINUTE }
        );

        return (
            <TooltipTrigger placement={'bottom'}>
                <QuietActionButton
                    ref={ref}
                    width={15}
                    zIndex={1}
                    id={'credit-balance-button'}
                    aria-label={'credit balance status'}
                    onPress={onPress}
                    UNSAFE_className={UNSAFE_className}
                    colorMode={isDarkMode ? ColorMode.DARK : ColorMode.LIGHT}
                >
                    {organizationBalance && isBalanceLow(organizationBalance) && (
                        <div className={classes.cornerIndicator} aria-label={`low credit indicator`}></div>
                    )}

                    <CreditCard />
                </QuietActionButton>
                <Tooltip>Credit balance</Tooltip>
            </TooltipTrigger>
        );
    }
);

const CreditBalanceButtonFuxNotification = ({ isDarkMode }: { isDarkMode: boolean }) => {
    const triggerRef = useRef(null);
    const fuxState = useOverlayTriggerState({});
    const settings = useUserGlobalSettings();

    const fuxNotificationsConfig = getSettingsOfType(settings.config, FUX_NOTIFICATION_KEYS);
    const fuxNotificationsSettings = getSettingsOfType(settings.config, FUX_SETTINGS_KEYS);
    const isFuxNotificationEnabled =
        fuxNotificationsConfig[FUX_NOTIFICATION_KEYS.AUTO_TRAINING_NOTIFICATION]?.isEnabled;
    const firstAutoTrainedProject = fuxNotificationsSettings[FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID].value;
    const prevFuxEnabled = usePrevious(isFuxNotificationEnabled);

    const { useActiveUser } = useUsers();
    const { organizationId } = useOrganizationIdentifier();
    const { data: activeUser } = useActiveUser(organizationId);
    const { project } = useProject();
    const isFirstAutoTrainedProject = firstAutoTrainedProject === project.id;

    useEffect(() => {
        if (isFuxNotificationEnabled && prevFuxEnabled !== isFuxNotificationEnabled) {
            fuxState.open();
        } else if (!isFuxNotificationEnabled && prevFuxEnabled !== isFuxNotificationEnabled) {
            fuxState.close();
        }
    }, [fuxState, isFuxNotificationEnabled, prevFuxEnabled]);

    const handleCloseTrainingNotification = () => {
        isFuxNotificationEnabled &&
            settings.saveConfig({
                ...settings.config,
                [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL]: { isEnabled: false },
                [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_NOTIFICATION]: { isEnabled: false },
            });
    };

    return (
        <>
            <CreditBalanceButtonDefault
                ref={triggerRef}
                isDarkMode={isDarkMode}
                onPress={handleCloseTrainingNotification}
                UNSAFE_className={isFuxNotificationEnabled && isFirstAutoTrainedProject ? classes.fuxOpen : ''}
            />

            {isFirstAutoTrainedProject ? (
                <FuxNotification
                    state={fuxState}
                    docUrl={activeUser?.isAdmin ? paths.account.usage({ organizationId }) : undefined}
                    triggerRef={triggerRef}
                    placement={'bottom right'}
                    onClose={handleCloseTrainingNotification}
                >
                    The auto-training job has been started, <CreditsToConsume /> credits deducted.
                    {activeUser?.isAdmin ? ' Check your credit balance here.' : null}
                </FuxNotification>
            ) : (
                <></>
            )}
        </>
    );
};
