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

import { Flex } from '@adobe/react-spectrum';

import { Close, Info } from '../../../../../assets/icons';
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
