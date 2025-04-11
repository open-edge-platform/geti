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

import { Flex, Heading } from '@adobe/react-spectrum';

import {
    AnnotatorSettingsConfig,
    FEATURES_KEYS,
    SettingsKeys,
} from '../../../../../core/user-settings/dtos/user-settings.interface';
import { TabPanelItem } from './tab-panel-item/tab-panel-item.component';

interface ActiveLearningSettingsProps {
    config: AnnotatorSettingsConfig;
    handleToggleFeature: (isEnabled: boolean, feature: SettingsKeys) => void;
}

export const ActiveLearningSettings = ({ config, handleToggleFeature }: ActiveLearningSettingsProps) => {
    return (
        <>
            <Heading marginTop={0} marginBottom={'size-200'}>
                Options
            </Heading>
            <Flex direction='column' gap='size-100'>
                <TabPanelItem
                    label={'Show Predictions'}
                    config={config}
                    settingKey={FEATURES_KEYS.INITIAL_PREDICTION}
                    handleToggleFeature={handleToggleFeature}
                />
            </Flex>
        </>
    );
};
