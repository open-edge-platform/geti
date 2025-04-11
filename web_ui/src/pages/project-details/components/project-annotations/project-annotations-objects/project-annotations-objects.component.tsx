// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex } from '@adobe/react-spectrum';
import { ResponsiveContainer } from 'recharts';

import { ObjectsPerLabelInterface } from '../../../../../core/statistics/dtos/dataset-statistics.interface';
import { CardContent } from '../../../../../shared/components/card-content/card-content.component';
import { BarHorizontalChart } from '../../../../../shared/components/charts/bar-horizontal-chart/bar-horizontal-chart.component';
import { Colors } from '../../../../../shared/components/charts/chart.interface';
import { FullscreenAction } from '../../../../../shared/components/fullscreen-action/fullscreen-action.component';
import { ProjectGridArea } from '../project-grid-area.interface';
import { formatToChartData, getColors, reorderObjectsLabels } from './utils';

interface ProjectAnnotationsObjectsProps extends ProjectGridArea {
    objectsPerLabel: ObjectsPerLabelInterface[];
}

export const ProjectAnnotationsObjects = ({
    objectsPerLabel,
    gridArea,
}: ProjectAnnotationsObjectsProps): JSX.Element => {
    const reorderedObjectsLabels = reorderObjectsLabels(objectsPerLabel);
    const data = formatToChartData(reorderedObjectsLabels);

    const colors: Colors[] = getColors(reorderedObjectsLabels);
    const title = 'Number of objects per label';

    return (
        <div style={{ gridArea }} aria-label={`${title} chart`}>
            <CardContent
                isDownloadable
                downloadableData={{ type: 'barChart', data }}
                title={title}
                actions={
                    <FullscreenAction
                        isDownloadable
                        title='Number of objects per label'
                        downloadableData={{ type: 'barChart', data }}
                    >
                        <BarHorizontalChart
                            title='Number of objects per label'
                            data={data}
                            colors={colors}
                            allowDecimals={false}
                            barSize={50}
                        />
                    </FullscreenAction>
                }
                height={'100%'}
            >
                <Flex height={'100%'} justifyContent={'center'} alignItems={'center'}>
                    <ResponsiveContainer id='objects-bar-horizontal-chart-id' width={'98%'} height={'98%'}>
                        <BarHorizontalChart
                            title='Number of objects per label'
                            data={data}
                            colors={colors}
                            allowDecimals={false}
                            yPadding={{ bottom: 10 }}
                            barSize={30}
                        />
                    </ResponsiveContainer>
                </Flex>
            </CardContent>
        </div>
    );
};
