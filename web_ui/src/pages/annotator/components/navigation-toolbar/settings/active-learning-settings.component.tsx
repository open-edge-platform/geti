// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
