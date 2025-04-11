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

import { Flex, View } from '@adobe/react-spectrum';

import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { ProjectsStorage } from './projects-storage/projects-storage.component';
import { StorageUsage } from './storage-usage/storage-usage.component';

export const Storage = (): JSX.Element => {
    const { FEATURE_FLAG_STORAGE_SIZE_COMPUTATION } = useFeatureFlags();

    return (
        <Flex flex={1} gap={'size-200'} height={'100%'}>
            <View minWidth={'size-5000'} flex={1}>
                <ProjectsStorage />
            </View>
            {FEATURE_FLAG_STORAGE_SIZE_COMPUTATION && (
                <View width={'size-3600'}>
                    <StorageUsage />
                </View>
            )}
        </Flex>
    );
};
