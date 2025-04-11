// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect, useState } from 'react';

import { Flex, Heading, Text, View } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import { useNavigate } from 'react-router-dom';

import { DatasetIdentifier } from '../../../core/projects/dataset.interface';
import { paths } from '../../../core/services/routes';
import { useViewMode } from '../../../hooks/use-view-mode/use-view-mode.hook';
import { MEDIA_CONTENT_BUCKET } from '../../../providers/media-upload-provider/media-upload.interface';
import { MediaViewModes } from '../../../shared/components/media-view-modes/media-view-modes.component';
import { INITIAL_VIEW_MODE, ViewModes } from '../../../shared/components/media-view-modes/utils';
import { ActionButtons } from '../components/action-buttons/action-buttons.component';
import { useCameraParams } from '../hooks/camera-params.hook';
import { useCameraStorage } from '../hooks/use-camera-storage.hook';
import { getSortingHandler, SortingOptions } from './../util';
import { MediaItemsList } from './components/media-items-list.component';
import { SortByDropdown } from './components/sort-by-dropdown.component';

const cameraPagePath = (datasetIdentifier: DatasetIdentifier) => paths.project.dataset.camera(datasetIdentifier);

export const MediaGallery = (): JSX.Element => {
    const navigate = useNavigate();
    const { hasDefaultLabel, defaultLabelId, ...rest } = useCameraParams();
    const { savedFilesQuery } = useCameraStorage();
    const [viewMode, setViewMode] = useViewMode(MEDIA_CONTENT_BUCKET.GENERIC, INITIAL_VIEW_MODE);
    const [sortingOption, setSortingOption] = useState(SortingOptions.MOST_RECENT);

    const sortingHandler = getSortingHandler(sortingOption);
    const screenshots = sortingHandler(savedFilesQuery?.data ?? []);

    useEffect(() => {
        if (isEmpty(screenshots)) {
            navigate(
                hasDefaultLabel ? `${cameraPagePath(rest)}?defaultLabelId=${defaultLabelId}` : cameraPagePath(rest)
            );
        }
    });

    return (
        <View padding={'size-250'} backgroundColor={'gray-75'}>
            <Flex direction={'row'} justifyContent={'space-between'}>
                <Flex direction={'column'}>
                    <Heading level={6} UNSAFE_style={{ fontWeight: '700' }} margin={0}>
                        {/* TODO: Change to "Images and videos once we support videos" */}
                        Images
                    </Heading>
                    <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-700)' }}>View all captures</Text>
                </Flex>

                <ActionButtons canGoToCameraPage />
            </Flex>

            <View
                overflow={'auto'}
                padding={'size-300'}
                marginTop={'size-275'}
                backgroundColor={'gray-50'}
                height={`calc(100vh - size-2000)`}
            >
                <Flex justifyContent={'space-between'}>
                    <SortByDropdown onSelect={setSortingOption} />
                    <Flex gap={'size-100'} alignItems={'center'}>
                        <Text>{viewMode} </Text>
                        <MediaViewModes
                            viewMode={viewMode}
                            setViewMode={setViewMode}
                            items={[ViewModes.LARGE, ViewModes.MEDIUM, ViewModes.SMALL]}
                        />
                    </Flex>
                </Flex>

                <MediaItemsList viewMode={viewMode} screenshots={screenshots} />
            </View>
        </View>
    );
};
