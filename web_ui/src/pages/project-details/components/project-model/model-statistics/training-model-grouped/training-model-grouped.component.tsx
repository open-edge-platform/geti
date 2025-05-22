// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useState } from 'react';

import { Flex, Item, Picker } from '@geti/ui';

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
