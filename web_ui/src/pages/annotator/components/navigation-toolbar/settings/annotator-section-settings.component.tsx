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

interface AnnotatorSectionSettingsProps {
    isSingleClassification: boolean;
    config: AnnotatorSettingsConfig;
    handleToggleFeature: (isEnabled: boolean, feature: SettingsKeys) => void;
}

const options = [
    { label: 'Annotations/Predictions', settingKey: FEATURES_KEYS.ANNOTATION_PANEL },
    { label: 'Counting', settingKey: FEATURES_KEYS.COUNTING_PANEL },
    { label: 'Dataset/Testing set/Active set', settingKey: FEATURES_KEYS.DATASET_PANEL },
];

export const AnnotatorSectionSettings = ({
    config,
    isSingleClassification,
    handleToggleFeature,
}: AnnotatorSectionSettingsProps) => {
    const filteredOptions = options.filter(({ settingKey }) =>
        isSingleClassification ? settingKey !== FEATURES_KEYS.COUNTING_PANEL : true
    );

    return (
        <>
            <Heading marginTop={0} marginBottom={'size-200'}>
                Availability
            </Heading>
            <Flex direction='column' gap='size-100'>
                {filteredOptions.map(({ label, settingKey }) => (
                    <TabPanelItem
                        key={`${settingKey}-${label}`}
                        label={label}
                        config={config}
                        settingKey={settingKey}
                        handleToggleFeature={handleToggleFeature}
                    />
                ))}
            </Flex>
        </>
    );
};
