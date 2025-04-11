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

import { ComponentProps } from 'react';

import { Flex, Text } from '@adobe/react-spectrum';

import { ProjectProps } from '../../../../core/projects/project.interface';
import { BarHorizontalChart } from '../../../../shared/components/charts/bar-horizontal-chart/bar-horizontal-chart.component';
import { getFileSize } from '../../../../shared/utils';

interface ProjectStorageChartProps {
    projects: ProjectProps[];
}

type BarHorizontalChartProps = ComponentProps<typeof BarHorizontalChart>;

const formatTooltipMessage: BarHorizontalChartProps['formatTooltipMessage'] = ({ value, label }) => {
    return (
        <Flex direction={'column'}>
            <Text>Project: {label}</Text>
            <Text>Size: {getFileSize(Number(value))}</Text>
        </Flex>
    );
};

const xTickFormatter: BarHorizontalChartProps['xTickFormatter'] = (value) => {
    return getFileSize(Number(value));
};

export const ProjectStorageChart = ({ projects }: ProjectStorageChartProps) => {
    const data = projects.map(({ name, storageInfo }) => ({
        name,
        value: storageInfo.size,
    }));

    return (
        <BarHorizontalChart
            title={'Size of'}
            data={data}
            formatTooltipMessage={formatTooltipMessage}
            xTickFormatter={xTickFormatter}
            ariaLabel={'Projects storage chart'}
        />
    );
};
