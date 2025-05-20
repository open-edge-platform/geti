// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@geti/ui';
import { Close, Info } from '@geti/ui/icons';

import { TUTORIAL_CARD_KEYS } from '../../../../../core/user-settings/dtos/user-settings.interface';
import { UserGlobalSettings, UseSettings } from '../../../../../core/user-settings/services/user-settings.interface';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';
import { dismissTutorial } from '../../../../../shared/components/tutorials/utils';

import classes from './quick-inference.module.scss';

interface LivePredictionNotificationProps {
    settings: UseSettings<UserGlobalSettings>;
}

export const LivePredictionNotification = ({ settings }: LivePredictionNotificationProps): JSX.Element => {
    const handleDismissTutorial = async () => {
        await dismissTutorial(TUTORIAL_CARD_KEYS.LIVE_PREDICTION_NOTIFICATION, settings);
    };

    return (
        <Flex
            maxWidth={'57rem'}
            alignItems={'center'}
            justifyContent={'space-between'}
            UNSAFE_className={classes.livePredictionNotification}
            gap={'size-100'}
        >
            <Flex alignItems={'start'}>
                <div>
                    <Info
                        className={classes.infoIcon}
                        style={{ marginRight: 'var(--spectrum-global-dimension-size-100)' }}
                    />
                </div>
                <Flex wrap={'wrap'}>
                    Upload an image that you would like to test with your active model right away.
                </Flex>
            </Flex>
            <QuietActionButton onPress={handleDismissTutorial} isDisabled={settings.isSavingConfig}>
                <Close />
            </QuietActionButton>
        </Flex>
    );
};
