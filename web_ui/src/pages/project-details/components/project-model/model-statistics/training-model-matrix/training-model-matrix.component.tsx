// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useRef, useState } from 'react';

import { Flex, Item, Picker } from '@geti/ui';
import { StyleProps } from '@react-types/shared';

import { ModelStatisticsBase } from '../../../../../../core/statistics/dtos/model-statistics.interface';
import { TrainModelStatisticsConfusionMatrix } from '../../../../../../core/statistics/model-statistics.interface';
import { CardContent } from '../../../../../../shared/components/card-content/card-content.component';
import { FullscreenAction } from '../../../../../../shared/components/fullscreen-action/fullscreen-action.component';
import { ConfusionMatrixZoom } from './confusion-matrix-zoom/confusion-matrix-zoom.component';

type TrainingModelMatrixProps = TrainModelStatisticsConfusionMatrix & ModelStatisticsBase & StyleProps;

export const TrainingModelMatrix = ({
    value,
    header,
    gridColumn,
    gridRow,
}: TrainingModelMatrixProps & StyleProps): JSX.Element => {
    const { matrixData, columnHeader, rowHeader } = value;

    const [selectedConfusionMatrixKey, setSelectedConfusionMatrix] = useState<string>(matrixData[0].key);
    const ref = useRef<HTMLDivElement>(null);

    const confusionMatrix = matrixData.filter(({ key }) => selectedConfusionMatrixKey === (key as Key))[0];
    const onSelectionConfusionMatrix = (selectedKey: Key): void => {
        setSelectedConfusionMatrix(String(selectedKey));
    };

    const size = confusionMatrix.matrixValues.length;

    const pickerComponent = (
        <Picker
            aria-label='Select a confusion matrix'
            items={matrixData}
            selectedKey={selectedConfusionMatrixKey}
            onSelectionChange={onSelectionConfusionMatrix}
        >
            {(item) => (
                <Item key={item.key} textValue={item.header}>
                    {item.header}
                </Item>
            )}
        </Picker>
    );

    const confusionMatrixData = {
        ...confusionMatrix,
        rowHeader,
        columnHeader,
    };

    return (
        <CardContent
            isDownloadable
            title={header}
            gridRow={gridRow}
            gridColumn={gridColumn}
            styles={{ height: size < 11 ? 'fit-content' : 'auto' }}
            downloadableData={{ type: 'matrix', data: confusionMatrixData }}
            actions={
                <Flex>
                    {pickerComponent}
                    <FullscreenAction
                        isDownloadable
                        title={header}
                        downloadableData={{ type: 'matrix', data: confusionMatrixData }}
                    >
                        <ConfusionMatrixZoom
                            title={header}
                            {...confusionMatrixData}
                            size={size}
                            matrixValues={confusionMatrix.matrixValues}
                        />
                    </FullscreenAction>
                </Flex>
            }
            height={'100%'}
        >
            <div
                ref={ref}
                style={{
                    height: 'calc(100% - var(--spectrum-global-dimension-size-250))',
                    minHeight: 0,
                    display: 'flex',
                    justifyContent: 'center',
                }}
            >
                <Flex
                    justifyContent={'center'}
                    direction={'column'}
                    alignItems={'center'}
                    height={'100%'}
                    minHeight={0}
                    marginTop={'size-250'}
                    width={'70%'}
                >
                    <ConfusionMatrixZoom
                        title={header}
                        {...confusionMatrixData}
                        size={size}
                        matrixValues={confusionMatrix.matrixValues}
                    />
                </Flex>
            </div>
        </CardContent>
    );
};
