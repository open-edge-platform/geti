// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { dimensionValue } from '@react-spectrum/utils';
import { Label, Pie, PieChart } from 'recharts';

import { getProgressScoreColor } from '../../../../../../../shared/utils';

type AccuracyHalfDonutChartSize = 'S' | 'M' | 'L' | 'XL';

const accuracyMeterSizeMap: Record<
    AccuracyHalfDonutChartSize,
    {
        fontSize: string | undefined;
        fontWeight: number;
        width: number;
        height: number;
        withPercentStyle: boolean;
    }
> = {
    S: {
        fontSize: dimensionValue('size-150'),
        fontWeight: 400,
        width: 45,
        height: 45,
        withPercentStyle: false,
    },
    M: {
        fontSize: dimensionValue('size-200'),
        fontWeight: 500,
        width: 70,
        height: 70,
        withPercentStyle: true,
    },
    L: {
        fontSize: dimensionValue('size-200'),
        fontWeight: 700,
        width: 90,
        height: 90,
        withPercentStyle: true,
    },
    XL: {
        fontSize: dimensionValue('size-300'),
        fontWeight: 700,
        width: 130,
        height: 130,
        withPercentStyle: true,
    },
};

interface AccuracyHalfDonutChartProps {
    id?: string;
    value: number;
    title?: string;
    isDisabled?: boolean;
    ariaLabel?: string;
    size?: AccuracyHalfDonutChartSize;
}

export const AccuracyHalfDonutChart = ({
    value,
    title,
    isDisabled,
    id,
    ariaLabel = 'Accuracy half donut chart',
    size = 'L',
}: AccuracyHalfDonutChartProps): JSX.Element => {
    const modelAccuracy = Math.round(value * 100);
    const remainingValue = Math.round((1 - value) * 100);

    // Known issue with 'recharts'. If the value is 0 then the value and title won't be rendered.
    // So here we're setting value to 0.1 in case the actual value is 0. The value is rounded so
    // it will correctly render "0%".
    const modelAccuracyChartValue = modelAccuracy === 0 ? 0.1 : modelAccuracy;

    const chartSizeConfig = accuracyMeterSizeMap[size];

    const remainingData = [
        {
            name: 'remaining-value',
            value: remainingValue,
            color: 'var(--spectrum-global-color-gray-300)',
        },
    ];

    const modelAccuracyData = [
        {
            name: 'accuracy-value',
            value: modelAccuracyChartValue,
            color: isDisabled ? 'var(--spectrum-global-color-gray-500)' : getProgressScoreColor(modelAccuracy),
        },
    ];

    return (
        <PieChart height={chartSizeConfig.height} width={chartSizeConfig.width}>
            <Pie
                dataKey='value'
                data={remainingData}
                stroke='none'
                startAngle={180}
                endAngle={0}
                fill={remainingData[0].color}
                innerRadius={'70%'}
                outerRadius={'100%'}
                id={`accuracy-progress-remaining-${id}-id`}
                data-testid={`accuracy-progress-remaining-${id}-id`}
                isAnimationActive={false}
            />
            <Pie
                dataKey='value'
                data={modelAccuracyData}
                stroke='none'
                startAngle={180}
                endAngle={180 - (180 * modelAccuracyChartValue) / 100}
                innerRadius={'70%'}
                outerRadius={'100%'}
                id={`accuracy-progress-${id}-id`}
                data-testid={`accuracy-progress-${id}-id`}
                fill={modelAccuracyData[0].color}
                aria-label={ariaLabel}
                aria-valuenow={modelAccuracy}
                // we don't want to show animation in test since it increases the execution time (we would need to
                // waitFor element to be rendered etc.)
                isAnimationActive={process.env.NODE_ENV !== 'test'}
            >
                <Label
                    position='center'
                    fontSize={chartSizeConfig.fontSize}
                    fontWeight={chartSizeConfig.fontWeight}
                    fill={
                        isDisabled ? 'var(--spectrum-global-color-gray-500)' : 'var(--spectrum-global-color-gray-800)'
                    }
                    id={'accuracy-half-donut-label-id'}
                    aria-label={`${title ?? 'Model score'} value`}
                >
                    {`${modelAccuracy}${chartSizeConfig.withPercentStyle ? '%' : ''}`}
                </Label>
                {title && (
                    <Label
                        position='center'
                        dy={20}
                        fill={
                            isDisabled
                                ? 'var(--spectrum-global-color-gray-500)'
                                : 'var(--spectrum-global-color-gray-800)'
                        }
                        fontSize={dimensionValue('size-150')}
                    >
                        {title}
                    </Label>
                )}
            </Pie>
        </PieChart>
    );
};
