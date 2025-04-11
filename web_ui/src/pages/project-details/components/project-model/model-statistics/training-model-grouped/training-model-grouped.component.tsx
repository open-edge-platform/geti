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

import { Key, useState } from 'react';

import { Flex, Item, Picker } from '@adobe/react-spectrum';

import {
    TrainingModelBarRadialChart,
    TrainingModelStatisticsGroup,
} from '../../../../../../core/statistics/model-statistics.interface';
import { CardContent } from '../../../../../../shared/components/card-content/card-content.component';
import { FullscreenAction } from '../../../../../../shared/components/fullscreen-action/fullscreen-action.component';
import TrainingModelBarChart from '../training-model-bar-chart/training-model-bar-chart.component';

export const TrainingModelGrouped = ({ header, values }: TrainingModelStatisticsGroup): JSX.Element => {
    const [selectedChart, setSelectedChart] = useState<TrainingModelBarRadialChart>(values[0]);

    const onSelectionChange = (key: Key) => {
        const foundByKey = values.find((value) => getKey(value) === key);

        foundByKey && setSelectedChart(foundByKey);
    };

    const getKey = (chart: TrainingModelBarRadialChart): string => {
        return chart.value[0].key;
    };

    const getValue = (chart: TrainingModelBarRadialChart): string => {
        return chart.value[0].header;
    };

    const downloadableData = selectedChart.value.map(({ value, header: labelHeader }) => ({
        name: labelHeader,
        value,
    }));

    return (
        <CardContent
            isDownloadable
            downloadableData={{ type: 'barChart', data: downloadableData }}
            title={header}
            actions={
                <Flex>
                    <Picker
                        aria-label={'Select'}
                        items={values}
                        selectedKey={getKey(selectedChart)}
                        onSelectionChange={onSelectionChange}
                    >
                        {(item) => (
                            <Item key={getKey(item)} textValue={getValue(item)}>
                                {getValue(item)}
                            </Item>
                        )}
                    </Picker>
                    <FullscreenAction
                        isDownloadable
                        title={header}
                        downloadableData={{ type: 'barChart', data: downloadableData }}
                    >
                        <TrainingModelBarChart
                            key={selectedChart.key}
                            type={selectedChart.type}
                            header={selectedChart.header}
                            value={selectedChart.value}
                            inCard={false}
                        />
                    </FullscreenAction>
                </Flex>
            }
            height={'100%'}
        >
            <TrainingModelBarChart
                key={selectedChart.key}
                type={selectedChart.type}
                header={selectedChart.header}
                value={selectedChart.value}
                inCard={false}
            />
        </CardContent>
    );
};
