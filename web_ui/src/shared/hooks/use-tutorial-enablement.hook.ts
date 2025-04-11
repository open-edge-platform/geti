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
