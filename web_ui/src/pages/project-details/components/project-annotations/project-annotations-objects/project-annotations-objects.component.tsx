// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@geti/ui';
import { ResponsiveContainer } from 'recharts';

import { ObjectsPerLabelInterface } from '../../../../../core/statistics/dtos/dataset-statistics.interface';
import { CardContent } from '../../../../../shared/components/card-content/card-content.component';
import { Colors } from '../../../../../shared/components/charts/chart.interface';
import { FullscreenAction } from '../../../../../shared/components/fullscreen-action/fullscreen-action.component';
import { InfoTooltip } from '../../../../../shared/components/info-tooltip/info-tooltip.component';
import { ProjectGridArea } from '../project-grid-area.interface';
import { AnnotationObjectsBarHorizontalChart } from './annotations-objects-bar-horizontal-chart/annotations-objects-bar-horizontal-chart.component';
import { formatToChartData, getColors, reorderObjectsLabels } from './utils';

interface ProjectAnnotationsObjectsProps extends ProjectGridArea {
    objectsPerLabel: ObjectsPerLabelInterface[];
}

const ActionTooltip = () => {
    return (
        <InfoTooltip
            tooltipText={
                "Click on a bar to view datasets filtered by this label. You'll be redirected to a page showing only " +
                'media items tagged with the selected label.'
            }
        />
    );
};

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
                titleActions={<ActionTooltip />}
                actions={
                    <FullscreenAction
                        isDownloadable
                        title='Number of objects per label'
                        downloadableData={{ type: 'barChart', data }}
                    >
                        <AnnotationObjectsBarHorizontalChart data={data} colors={colors} barSize={50} title={title} />
                    </FullscreenAction>
                }
                height={'100%'}
            >
                <Flex height={'100%'} justifyContent={'center'} alignItems={'center'}>
                    <ResponsiveContainer id='objects-bar-horizontal-chart-id' width={'98%'} height={'98%'}>
                        <AnnotationObjectsBarHorizontalChart
                            data={data}
                            colors={colors}
                            yPadding={{ bottom: 10 }}
                            barSize={30}
                            title={title}
                        />
                    </ResponsiveContainer>
                </Flex>
            </CardContent>
        </div>
    );
};
