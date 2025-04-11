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

import { Key, useRef, useState } from 'react';

import { Flex, Item, Picker } from '@adobe/react-spectrum';
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
