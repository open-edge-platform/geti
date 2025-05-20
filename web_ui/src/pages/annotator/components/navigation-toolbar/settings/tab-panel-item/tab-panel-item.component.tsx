// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Switch } from '@geti/ui';

import {
    AnnotatorSettingsConfig,
    FEATURES_KEYS,
    SettingsFeature,
} from '../../../../../../core/user-settings/dtos/user-settings.interface';
import { InfoTooltip } from '../../../../../../shared/components/info-tooltip/info-tooltip.component';
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
