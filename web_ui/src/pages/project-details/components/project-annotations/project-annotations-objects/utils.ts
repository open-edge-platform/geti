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

import negate from 'lodash/negate';

import { ObjectsPerLabelInterface } from '../../../../../core/statistics/dtos/dataset-statistics.interface';
import { ChartData, Colors } from '../../../../../shared/components/charts/chart.interface';
import { convertColorToFadedColor } from '../../../../../shared/components/charts/utils';

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
