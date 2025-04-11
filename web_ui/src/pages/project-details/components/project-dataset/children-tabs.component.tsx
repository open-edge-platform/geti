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
import capitalize from 'lodash/capitalize';

import { GraphChart, Image } from '../../../../assets/icons';
import { TabItem } from '../../../../shared/components/tabs/tabs.interface';
import { ProjectAnnotationsStatistics } from '../project-annotations/project-annotations-statistics.component';
import { ProjectMedia } from '../project-media/project-media.component';
import { DatasetChapters } from './utils';

export const ChildrenTabs = (): TabItem[] => {
    return [
        {
            id: `${DatasetChapters.MEDIA}-id`,
            key: DatasetChapters.MEDIA,
            name: (
                <Flex alignItems={'center'} gap={'size-75'}>
                    <Image />
                    {capitalize(DatasetChapters.MEDIA)}
                </Flex>
            ),
            children: <ProjectMedia />,
        },
        {
            id: `${DatasetChapters.STATISTICS}-id`,
            key: DatasetChapters.STATISTICS,
            name: (
                <Flex alignItems={'center'} gap={'size-75'}>
                    <GraphChart />
                    {capitalize(DatasetChapters.STATISTICS)}
                </Flex>
            ),
            children: <ProjectAnnotationsStatistics />,
        },
    ];
};
