// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
