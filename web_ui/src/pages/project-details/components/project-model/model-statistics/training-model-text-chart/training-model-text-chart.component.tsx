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

import { Flex, Text } from '@adobe/react-spectrum';

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
