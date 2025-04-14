// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    ModelStatisticsBarDataDTO,
    ModelStatisticsBase,
    ModelStatisticsConfusionMatrixDataDTO,
    ModelStatisticsConfusionMatrixDTO,
    ModelStatisticsConfusionMatrixValueDTO,
    ModelStatisticsLineDataDTO,
    ModelStatisticsTextDataDTO,
} from './dtos/model-statistics.interface';

interface TrainingModelStatisticsConfusionMatrixData
    extends Pick<ModelStatisticsConfusionMatrixDataDTO, 'header' | 'key'> {
    columnNames: ModelStatisticsConfusionMatrixDataDTO['column_names'];
    rowNames: ModelStatisticsConfusionMatrixDataDTO['row_names'];
    matrixValues: ModelStatisticsConfusionMatrixDataDTO['matrix_values'];
}

export interface TrainModelStatisticsConfusionMatrixValue {
    rowHeader: ModelStatisticsConfusionMatrixValueDTO['row_header'];
    columnHeader: ModelStatisticsConfusionMatrixValueDTO['column_header'];
    matrixData: TrainingModelStatisticsConfusionMatrixData[];
}

export interface TrainModelStatisticsConfusionMatrix extends Omit<ModelStatisticsConfusionMatrixDTO, 'value'> {
    value: TrainModelStatisticsConfusionMatrixValue;
}

export type TrainingModelInfoType = ModelStatisticsBase & ModelStatisticsTextDataDTO;

interface TrainingModelLineChartProps extends ModelStatisticsBase, Pick<ModelStatisticsLineDataDTO, 'type'> {
    value: {
        lineData: ModelStatisticsLineDataDTO['value']['line_data'];
        xAxisLabel: ModelStatisticsLineDataDTO['value']['x_axis_label'];
        yAxisLabel: ModelStatisticsLineDataDTO['value']['y_axis_label'];
    };
}

export type TrainingModelLineChartType = ModelStatisticsBase & TrainingModelLineChartProps;

export type TrainingModelBarRadialChart = ModelStatisticsBase & ModelStatisticsBarDataDTO;

type TrainingModelStatisticsData =
    | ModelStatisticsTextDataDTO
    | ModelStatisticsBarDataDTO
    | TrainingModelLineChartType
    | TrainModelStatisticsConfusionMatrix;

export type TrainingModelStatistic = ModelStatisticsBase & TrainingModelStatisticsData;

export interface TrainingModelStatisticsGroup {
    header: string;
    key: string;
    type: 'group';
    values: TrainingModelBarRadialChart[];
}

export interface TrainingModelChartConfig {
    inCard?: boolean;
}

export type ModelMetrics = (TrainingModelStatisticsGroup | TrainingModelStatistic)[];
