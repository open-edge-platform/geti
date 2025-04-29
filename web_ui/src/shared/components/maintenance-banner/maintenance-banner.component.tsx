// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Content, Flex, Heading, View } from '@adobe/react-spectrum';
import dayjs from 'dayjs';

import { Alert, Close } from '../../../assets/icons';
import { useMaintenanceQuery } from '../../../core/maintenance/hooks/use-maintenance-query.hook';
import { GENERAL_SETTINGS_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../core/user-settings/hooks/use-global-settings.hook';
import { getSettingsOfType } from '../../../core/user-settings/utils';
import { QuietActionButton } from '../quiet-button/quiet-action-button.component';

import classes from './maintenance-banner.module.scss';

export const MaintenanceBanner = () => {
    const { data } = useMaintenanceQuery();
    const { saveConfig, config } = useUserGlobalSettings();

    if (!data) {
        return null;
    }

    const {
        maintenance: { enabled, window },
    } = data;

    const generalSettingsConfig = getSettingsOfType(config, GENERAL_SETTINGS_KEYS);
    const wasDismissedForTheCurrentMaintenanceWindow = window
        ? generalSettingsConfig[GENERAL_SETTINGS_KEYS.MAINTENANCE_BANNER]?.wasDismissed &&
          generalSettingsConfig[GENERAL_SETTINGS_KEYS.MAINTENANCE_BANNER]?.window?.start === window.start &&
          generalSettingsConfig[GENERAL_SETTINGS_KEYS.MAINTENANCE_BANNER]?.window?.end === window.end
        : false;

    if (!enabled || !window || wasDismissedForTheCurrentMaintenanceWindow) {
        return null;
    }

    const handleDismissBanner = () => {
        saveConfig({
            ...config,
            [GENERAL_SETTINGS_KEYS.MAINTENANCE_BANNER]: {
                wasDismissed: true,
                window: {
                    start: window.start,
                    end: window.end,
                },
            },
        });
    };

    const isSameDay = dayjs.unix(window.start).isSame(dayjs.unix(window.end), 'day');
    const fromTime = dayjs.unix(window.start).format('D of MMMM, HH:mm'); // e.g. 7 of November, 14:02

    // If the maintenance begins and ends on the same day, we only show the hour change, i.e.
    // "7 of November, 14:02 to 18:30"
    const toTime = dayjs.unix(window.end).format(isSameDay ? 'HH:mm' : 'D of MMMM, HH:mm');

    return (
        <View UNSAFE_className={classes.banner} id={'maintenance-banner-id'}>
            <Flex alignItems={'center'} justifyContent={'space-between'} marginBottom={'size-200'}>
                <Heading level={2} UNSAFE_className={classes.heading}>
                    <Flex alignItems={'center'}>
                        <Alert className={classes.alertIcon} />
                        Scheduled maintenance
                    </Flex>
                </Heading>
                <QuietActionButton
                    onPress={handleDismissBanner}
                    aria-label='dismiss banner'
                    UNSAFE_className={classes.closeButton}
                    id={'dismiss-maintenance-banner-id'}
                >
                    <Close />
                </QuietActionButton>
            </Flex>
            <Content UNSAFE_className={classes.content} id={'maintenance-banner-content-id'}>
                We will be performing a scheduled update from <b>{fromTime}</b> to <b>{toTime} UTC</b>. During this
                time, our platform will be unavailable. We apologize for any inconvenience.
            </Content>
        </View>
    );
};
