// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text } from '@geti/ui';

import { TrainingModelChartConfig } from '../../../../../../core/statistics/model-statistics.interface';
import { CardContent } from '../../../../../../shared/components/card-content/card-content.component';
import { withDownloadableHtml } from '../../../../../../shared/components/download-graph-menu/with-downloadable-svg.hoc';

import classes from './training-model-text-chart.module.scss';

interface TrainingModelTextChartProps extends TrainingModelChartConfig {
    value: string;
    header: string;
}

const ModelTextChart = ({ value }: Pick<TrainingModelTextChartProps, 'value'>): JSX.Element => {
    return (
        <Flex direction={'column'} gap={'size-65'} alignItems={'center'} justifyContent={'center'} height={'100%'}>
            <Text UNSAFE_className={classes.textChartValue}>{value}</Text>
        </Flex>
    );
};

const DownloadableModelTextChart = withDownloadableHtml(ModelTextChart);

export const TrainingModelTextChart = ({ value, header }: TrainingModelTextChartProps): JSX.Element => {
    return (
        <CardContent
            title={header}
            isDownloadable
            downloadableData={{ type: 'text', data: value, header }}
            height={'100%'}
        >
            <DownloadableModelTextChart value={value} title={header} />
        </CardContent>
    );
};
