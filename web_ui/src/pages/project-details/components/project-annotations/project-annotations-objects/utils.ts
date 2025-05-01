// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ChartData, Colors } from '@shared/components/charts/chart.interface';
import { convertColorToFadedColor } from '@shared/components/charts/utils';
import negate from 'lodash/negate';

import { ObjectsPerLabelInterface } from '../../../../../core/statistics/dtos/dataset-statistics.interface';

export const getColors = (objectsPerLabel: ObjectsPerLabelInterface[]): Colors[] =>
    objectsPerLabel.reduce<Colors[]>((prev, curr) => {
        const { color } = curr;
        const fadedColor = convertColorToFadedColor(color, 50);

        return [...prev, { color, fadedColor }];
    }, []);

//Note: we don't have is_empty here so we have to filter by names of empty labels
const isEmptyLabel = ({ name }: ObjectsPerLabelInterface) =>
    ['empty', 'no object', 'no class'].includes(name.toLowerCase());

export const reorderObjectsLabels = (objectsPerLabel: ObjectsPerLabelInterface[]) => {
    const emptyLabels = objectsPerLabel.filter(isEmptyLabel);
    const filteredLabels = objectsPerLabel.filter(negate(isEmptyLabel));
    return [...filteredLabels, ...emptyLabels];
};

export const formatToChartData = (objectsPerLabel: ObjectsPerLabelInterface[]) =>
    objectsPerLabel.map(
        ({ name, value }): ChartData => ({
            name,
            value,
        })
    );
