// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useRef } from 'react';

import isEmpty from 'lodash/isEmpty';

import { FUX_NOTIFICATION_KEYS, TUTORIAL_CARD_KEYS } from '../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../core/user-settings/hooks/use-global-settings.hook';
import {
    dismissAllTutorials,
    dismissTutorial,
    getTutorialAndFuxNotificationsConfig,
    handleChangeTutorial,
    resetAllTutorials,
} from '../components/tutorials/utils';

interface UseTutorialEnablement {
    close: () => Promise<void>;
    dismissAll: () => Promise<void>;
    isOpen: boolean;
    changeTutorial: (currentKey: FUX_NOTIFICATION_KEYS, changeToKey: FUX_NOTIFICATION_KEYS) => Promise<void>;
}

export const useTutorialEnablement = (
    tutorialKey: TUTORIAL_CARD_KEYS | FUX_NOTIFICATION_KEYS
): UseTutorialEnablement => {
    const settings = useUserGlobalSettings();
    const tutorialAndFuxNotificationConfig = getTutorialAndFuxNotificationsConfig(settings.config);
    const isOpen = tutorialKey ? tutorialAndFuxNotificationConfig[tutorialKey].isEnabled === true : false;
    const savingError = useRef<boolean>(false);

    const close = async (): Promise<void> => {
        if (tutorialKey === undefined || isEmpty(tutorialAndFuxNotificationConfig[tutorialKey])) {
            return;
        }

        try {
            dismissTutorial(tutorialKey, settings);
        } catch (_error: unknown) {
            savingError.current = true;
        }
    };

    const dismissAll = async (): Promise<void> => {
        try {
            await dismissAllTutorials(settings);
        } catch (_error: unknown) {
            savingError.current = true;
        }
    };

    const changeTutorial = async (
        currentKey: FUX_NOTIFICATION_KEYS,
        changeToKey: FUX_NOTIFICATION_KEYS
    ): Promise<void> => {
        if (
            currentKey === undefined ||
            isEmpty(tutorialAndFuxNotificationConfig[currentKey]) ||
            changeToKey === undefined ||
            isEmpty(tutorialAndFuxNotificationConfig[changeToKey])
        ) {
            return;
        }
        try {
            await handleChangeTutorial(currentKey, changeToKey, settings);
        } catch (_error: unknown) {
            savingError.current = true;
        }
    };

    return { close, isOpen, dismissAll, changeTutorial };
};

export const useResetAllTutorials = () => {
    const settings = useUserGlobalSettings();

    const resetAll = async (): Promise<void> => {
        await resetAllTutorials(settings);
    };

    return resetAll;
};
