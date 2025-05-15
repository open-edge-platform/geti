// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Grid, minmax, repeat, Text } from '@adobe/react-spectrum';

import { TruncatedTextWithTooltip } from '../../truncated-text/truncated-text.component';
import { convertColorToFadedColor, HexKeysType } from '../utils';
import { ConfusionMatrixProps } from './confusion-matrix.interface';

import classes from './confusion-matrix.module.scss';

const basicColor = '#0095CA';
const darkColor = '#242528';

const getColor = (value: number): string => {
    const roundedValue = Math.round(value * 100);
    const darkColorThreshold = 10;
    return roundedValue >= darkColorThreshold
        ? convertColorToFadedColor(basicColor, Math.round(value * 100) as HexKeysType)
        : darkColor;
};

export const ConfusionMatrix = ({
    columnHeader,
    rowHeader,
    columnNames,
    rowNames,
    matrixValues,
    size,
}: ConfusionMatrixProps): JSX.Element => {
    return (
        <Grid
            width={'100%'}
            rows={[repeat(size, minmax('size-1250', 'auto')), 'size-600', 'size-500']}
            columns={['size-500', 'size-2000', repeat(size, 'auto')]}
            UNSAFE_className={classes.confusionMatrixContainer}
            height={'100%'}
        >
            <Flex
                id={`${columnHeader}-id`}
                alignItems={'center'}
                justifyContent={'center'}
                gridArea={`1 / 1 / ${size + 1} / 1`}
            >
                <Flex
                    minWidth={'size-1700'}
                    UNSAFE_className={[classes.confusionMatrixColumnHeader, classes.confusionMatrixHeaders].join(' ')}
                    justifyContent={'center'}
                >
                    {columnHeader}
                </Flex>
            </Flex>
            {columnNames.map((columnName: string, index: number) => (
                <Flex
                    gridColumn={'2 / 3'}
                    gridRow={`${1 + index} / ${2 + index}`}
                    alignItems={'center'}
                    justifyContent={'center'}
                    key={columnName}
                >
                    <TruncatedTextWithTooltip UNSAFE_className={classes.confusionMatrixHeaders}>
                        {columnName}
                    </TruncatedTextWithTooltip>
                </Flex>
            ))}
            {matrixValues.map((row, rowIndex) =>
                row.map((value, index) => (
                    <Flex
                        alignItems={'center'}
                        justifyContent={'center'}
                        gridRow={`${rowIndex + 1}`}
                        gridColumn={`${3 + index} / ${4 + index}`}
                        key={`${columnNames[index % columnNames.length]}-${value}-${index}`}
                        UNSAFE_style={{ backgroundColor: getColor(value) }}
                    >
                        <Text>{value.toFixed(1)}</Text>
                    </Flex>
                ))
            )}
            {rowNames.map((rowName: string, index: number) => (
                <Flex
                    alignItems={'center'}
                    justifyContent={'center'}
                    gridRow={`${size + 1}`}
                    gridColumn={`${3 + index} / ${4 + index}`}
                    key={rowName}
                >
                    <span title={rowName} className={classes.confusionMatrixHeaders}>
                        {rowName}
                    </span>
                </Flex>
            ))}
            <Flex
                gridColumn={`3 / ${size + 3}`}
                gridRow={`${size + 2}`}
                alignItems={'center'}
                justifyContent={'center'}
                id={`${rowHeader}-id`}
                UNSAFE_className={classes.confusionMatrixHeaders}
            >
                <Text minWidth={'size-1700'} UNSAFE_className={classes.confusionMatrixHeaders}>
                    {rowHeader}
                </Text>
            </Flex>
        </Grid>
    );
};
