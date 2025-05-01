// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo, useState } from 'react';

import { Flex, Text } from '@adobe/react-spectrum';
import { CardContent } from '@shared/components/card-content/card-content.component';
import { PieChart } from '@shared/components/charts/pie-chart/pie-chart.component';
import { FullscreenAction } from '@shared/components/fullscreen-action/fullscreen-action.component';

import { isClassificationDomain } from '../../../../../core/projects/domains';
import { ObjectSizeDistribution } from '../../../../../core/statistics/services/dataset-statistics.interface';
import { useProject } from '../../../providers/project-provider/project-provider.component';
import { ProjectGridArea } from '../project-grid-area.interface';
import { DistributionChart } from './distribution-chart/distribution-chart.component';
import { ObjectsList } from './objects-list/objects-list.component';
import { getDistributionLabels } from './utils';

import classes from './object-size-distribution-wrapper.module.scss';

const MAX_OBJECT_SIZES_PER_LABEL = 1000;

interface ObjectSizeDistributionProps extends ProjectGridArea {
    objectSizeDistribution: ObjectSizeDistribution[];
}

export const ObjectSizeDistributionWrapper = ({
    gridArea,
    objectSizeDistribution,
}: ObjectSizeDistributionProps): JSX.Element => {
    const labels = useMemo(() => getDistributionLabels(objectSizeDistribution), [objectSizeDistribution]);
    const [selectedLabelKey, setSelectedLabelKey] = useState<string>(labels[0].name);

    const [selectedObjectDistribution] = objectSizeDistribution.filter(
        ({ labelName }) => labelName === selectedLabelKey
    );

    const { objectDistributionFromAspectRatio, aspectRatioThresholdWide, aspectRatioThresholdTall } =
        selectedObjectDistribution;

    const { tall, balanced, wide } = objectDistributionFromAspectRatio;

    const pieChartData = [
        { name: 'Tall', value: tall, color: 'var(--tall-distribution)' },
        { name: 'Wide', value: wide, color: 'var(--wide-distribution)' },
        { name: 'Balanced', value: balanced, color: 'var(--balanced-distribution)' },
    ];
    const objectSizes = [...pieChartData.map(({ name, color }) => ({ name, color })), { name: 'Near mean', color: '' }];

    const { isSingleDomainProject } = useProject();

    const CHART_TITLE = isSingleDomainProject(isClassificationDomain)
        ? 'Image size distribution'
        : 'Object size distribution';

    const limitedDueToSize =
        selectedObjectDistribution.objectDistributionFromAspectRatio.balanced === MAX_OBJECT_SIZES_PER_LABEL ||
        selectedObjectDistribution.objectDistributionFromAspectRatio.tall === MAX_OBJECT_SIZES_PER_LABEL ||
        selectedObjectDistribution.objectDistributionFromAspectRatio.wide === MAX_OBJECT_SIZES_PER_LABEL;

    return (
        <div style={{ gridArea }} aria-label={`${CHART_TITLE} chart`}>
            <CardContent
                isDownloadable
                height={'100%'}
                downloadableData={{
                    type: 'default',
                    header: ['Width', 'Height'],
                    data: selectedObjectDistribution.sizeDistribution,
                }}
                title={CHART_TITLE}
                actions={
                    <FullscreenAction
                        isDownloadable
                        title={CHART_TITLE}
                        downloadableData={{
                            type: 'default',
                            header: ['Width', 'Height'],
                            data: selectedObjectDistribution.sizeDistribution,
                        }}
                    >
                        <DistributionChart
                            title={CHART_TITLE}
                            legend={objectSizes}
                            objectSizeDistribution={selectedObjectDistribution}
                        />
                    </FullscreenAction>
                }
                styles={{ height: 'fit-content' }}
            >
                {limitedDueToSize && (
                    <Flex alignSelf={'center'} UNSAFE_className={classes.limitedNotice}>
                        <Text>
                            The object size distribution dataset was sampled to {MAX_OBJECT_SIZES_PER_LABEL} due to the
                            size of the dataset.
                        </Text>
                    </Flex>
                )}
                <Flex
                    height={'100%'}
                    justifyContent={'center'}
                    UNSAFE_className={classes.objectDistributionWrapper}
                    width={'100%'}
                >
                    <Flex
                        justifyContent={'center'}
                        direction={'column'}
                        height={'100%'}
                        width={'100%'}
                        gap={'size-675'}
                    >
                        <ObjectsList
                            labels={labels}
                            objectSizes={objectSizes}
                            selectedLabelKey={selectedLabelKey}
                            setSelectedLabelKey={setSelectedLabelKey}
                        />
                        {aspectRatioThresholdWide !== null && !!aspectRatioThresholdTall !== null ? (
                            <PieChart
                                title={CHART_TITLE}
                                data={pieChartData}
                                legend={objectSizes}
                                ariaLabel={'Number of objects in Object size distribution'}
                            />
                        ) : (
                            <PieChart
                                title={CHART_TITLE}
                                legend={objectSizes}
                                data={[{ name: null, value: 100, color: 'var(--spectrum-global-color-gray-300)' }]}
                                ariaLabel={'Number of objects in Object size distribution'}
                            />
                        )}
                    </Flex>
                    <DistributionChart
                        title={CHART_TITLE}
                        legend={objectSizes}
                        objectSizeDistribution={selectedObjectDistribution}
                    />
                </Flex>
            </CardContent>
        </div>
    );
};
