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

interface ModelChartColor {
    color?: string;
}

type ChartType = 'line' | 'bar' | 'radial_bar' | 'matrix' | 'text';

export interface ModelStatisticsBase {
    header: string;
    key: string;
}

export interface ModelStatisticsBarDataDTO {
    type: Extract<ChartType, 'radial_bar' | 'bar'>;
    value: ({
        header: string;
        key: string;
        value: number;
    } & ModelChartColor)[];
}

interface ModelStatisticsLinePointsDataDTO extends ModelStatisticsBase, ModelChartColor {
    points: {
        x: number;
        y: number;
    }[];
}

export interface ModelStatisticsLineDataDTO {
    type: Extract<ChartType, 'line'>;
    value: {
        line_data: ModelStatisticsLinePointsDataDTO[];
        x_axis_label: string;
        y_axis_label: string;
    };
}

export interface ModelStatisticsTextDataDTO {
    type: Extract<ChartType, 'text'>;
    value: string;
}

export interface ModelStatisticsConfusionMatrixDataDTO extends ModelStatisticsBase {
    column_names: string[];
    row_names: string[];
    matrix_values: number[][];
}

export interface ModelStatisticsConfusionMatrixValueDTO {
    row_header: string;
    column_header: string;
    matrix_data: ModelStatisticsConfusionMatrixDataDTO[];
}

export interface ModelStatisticsConfusionMatrixDTO {
    type: Extract<ChartType, 'matrix'>;
    value: ModelStatisticsConfusionMatrixValueDTO;
}

export type ModelStatisticsDataDTO =
    | ModelStatisticsTextDataDTO
    | ModelStatisticsBarDataDTO
    | ModelStatisticsLineDataDTO
    | ModelStatisticsConfusionMatrixDTO;

export type ModelStatisticsDTO = ModelStatisticsDataDTO & ModelStatisticsBase;
