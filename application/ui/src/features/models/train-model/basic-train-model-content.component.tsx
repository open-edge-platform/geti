// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Divider, Flex, View } from '@geti-ui/ui';

import { ModelArchitecturesList } from './model-architectures-list/model-architectures-list.component';
import { SelectDatasetRevision } from './select-dataset-revision.component';
import { SelectModelRevision } from './select-model-revision.component';
import { SelectTrainingDevice } from './select-training-device/select-training-device.component';
import { TimmModelConfiguration } from './timm-model-configuration/timm-model-configuration.component';

export const BasicTrainModelContent = () => {
    // TODO: Update this once the backend part is done
    const isTIMMModelSelected = false;

    return (
        <View backgroundColor={'gray-50'} height={'100%'}>
            <Flex height={'100%'} direction={'column'} gap={'size-300'}>
                <View flex={1} minHeight={0} overflow={'auto'}>
                    <ModelArchitecturesList />
                </View>

                <Divider size={'S'} width={'100%'} />

                <Flex direction={'column'} gap={'size-300'}>
                    {isTIMMModelSelected && <TimmModelConfiguration />}

                    <Flex gap={'size-300'} width={'100%'}>
                        <SelectTrainingDevice />
                        <SelectDatasetRevision />
                        <SelectModelRevision />
                    </Flex>
                </Flex>
            </Flex>
        </View>
    );
};
