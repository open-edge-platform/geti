// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
