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

import { Flex } from '@adobe/react-spectrum';

import {
    AnnotatorSettingsConfig,
    FEATURES_KEYS,
    SettingsFeature,
} from '../../../../../../core/user-settings/dtos/user-settings.interface';
import { InfoTooltip } from '../../../../../../shared/components/info-tooltip/info-tooltip.component';
import { Switch } from '../../../../../../shared/components/switch/switch.component';
import { idMatchingFormat } from '../../../../../../test-utils/id-utils';

interface TabPanelItemProps {
    label: string;
    config: AnnotatorSettingsConfig;
    settingKey: FEATURES_KEYS;
    handleToggleFeature: (isEnabled: boolean, feature: FEATURES_KEYS) => void;
}

export const TabPanelItem = ({ label, config, settingKey, handleToggleFeature }: TabPanelItemProps): JSX.Element => {
    const featureConfig = config[settingKey] as SettingsFeature;

    return (
        <Flex direction={'row'} justifyContent='space-between' alignContent={'center'} alignItems={'center'}>
            <Switch
                aria-label={label}
                data-testid={`${idMatchingFormat(featureConfig.title)}-panel-switch-id`}
                isSelected={featureConfig.isEnabled}
                onChange={(isToggled) => handleToggleFeature(isToggled, settingKey)}
            >
                {label}
            </Switch>
            {'tooltipDescription' in featureConfig && (
                <InfoTooltip
                    id={`toggle-info-${idMatchingFormat(featureConfig.title)}-list`}
                    tooltipText={featureConfig.tooltipDescription}
                />
            )}
        </Flex>
    );
};
