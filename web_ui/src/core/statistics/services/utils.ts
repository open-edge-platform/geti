// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { groupBy } from 'lodash-es';

import { idMatchingFormat } from '../../../test-utils/id-utils';
import { AllTaskDatasetStatisticsDTO, DatasetStatisticsDTO } from '../dtos/dataset-statistics.interface';
import {
    ModelStatisticsBarDataDTO,
    ModelStatisticsBase,
    ModelStatisticsConfusionMatrixDTO,
    ModelStatisticsDataDTO,
    ModelStatisticsDTO,
    ModelStatisticsLineDataDTO,
} from '../dtos/model-statistics.interface';
import {
    TrainingModelBarRadialChart,
    TrainingModelStatistic,
    TrainingModelStatisticsGroup,
    TrainModelStatisticsConfusionMatrixValue,
} from '../model-statistics.interface';
import { AllTasksDatasetStatistics, DatasetStatistics } from './dataset-statistics.interface';

const isBarChartType = (
    statistics: ModelStatisticsDataDTO
): statistics is ModelStatisticsBarDataDTO & ModelStatisticsBase => {
    return statistics.type === 'bar';
};

export const getAllTaskDatasetStatisticsDTO = (data: AllTaskDatasetStatisticsDTO): AllTasksDatasetStatistics => {
    return {
        overview: {
            videos: data.overview.videos,
            images: data.overview.images,
            annotatedFrames: data.overview.annotated_frames,
            annotatedImages: data.overview.annotated_images,
            annotatedVideos: data.overview.annotated_videos,
        },
        tasks: data.tasks.map(({ task_id, ...task }) => ({ id: task_id, ...getDatasetStatisticsEntity(task) })),
    };
};

export const getDatasetStatisticsEntity = (statistics: DatasetStatisticsDTO): DatasetStatistics => {
    const {
        annotated_videos,
        annotated_images,
        annotated_frames,
        videos,
        images,
        objects_per_label,
        object_size_distribution_per_label,
    } = statistics;

    return {
        videos,
        images,
        annotatedFrames: annotated_frames,
        annotatedImages: annotated_images,
        annotatedVideos: annotated_videos,
        objectsPerLabel: objects_per_label,
        objectSizeDistributionPerLabel: object_size_distribution_per_label.map(
            ({
                color,
                id,
                name,
                aspect_ratio_threshold_tall,
                aspect_ratio_threshold_wide,
                cluster_center,
                cluster_width_height,
                object_distribution_from_aspect_ratio,
                size_distribution,
            }) => ({
                labelColor: color,
                labelId: id,
                labelName: name,
                aspectRatioThresholdTall: aspect_ratio_threshold_tall,
                aspectRatioThresholdWide: aspect_ratio_threshold_wide,
                objectDistributionFromAspectRatio: object_distribution_from_aspect_ratio,
                sizeDistribution: size_distribution,
                clusterCenter: cluster_center,
                clusterWidthHeight: cluster_width_height,
            })
        ),
    };
};

const getValueForMatrix = (modelStatisticDTO: ModelStatisticsConfusionMatrixDTO & ModelStatisticsBase) => {
    const { header, value, key, type } = modelStatisticDTO;
    const { row_header, column_header, matrix_data } = value;
    const convertedValue: TrainModelStatisticsConfusionMatrixValue = {
        rowHeader: row_header,
        columnHeader: column_header,
        matrixData: matrix_data.map(({ row_names, column_names, matrix_values, ...rest }) => ({
            ...rest,
            columnNames: column_names,
            rowNames: row_names,
            matrixValues: matrix_values,
        })),
    };

    return {
        type,
        key: idMatchingFormat(key),
        header,
        value: convertedValue,
    };
};

const getValueForLine = (modelStatisticDTO: ModelStatisticsLineDataDTO & ModelStatisticsBase) => {
    const {
        value: { line_data, x_axis_label, y_axis_label },
        ...rest
    } = modelStatisticDTO;
    return {
        ...rest,
        value: {
            lineData: line_data,
            xAxisLabel: x_axis_label,
            yAxisLabel: y_axis_label,
        },
    };
};

const getValueForBar = (
    modelStatisticDTO: ModelStatisticsBarDataDTO & ModelStatisticsBase
): TrainingModelBarRadialChart => {
    const { value, key, type, header } = modelStatisticDTO;

    return {
        key: idMatchingFormat(key),
        value,
        type,
        header,
    };
};

const getStatisticEntity = (modelStatisticDTO: ModelStatisticsDTO): TrainingModelStatistic => {
    switch (modelStatisticDTO.type) {
        case 'matrix':
            return getValueForMatrix(modelStatisticDTO);
        case 'line':
            return getValueForLine(modelStatisticDTO);
        default:
            return {
                ...modelStatisticDTO,
                key: idMatchingFormat(modelStatisticDTO.key),
            };
    }
};

export const getModelStatisticsEntity = (
    modelStatisticsDTO: ModelStatisticsDTO[]
): (TrainingModelStatistic | TrainingModelStatisticsGroup)[] => {
    const groupedCharts = groupBy(modelStatisticsDTO, 'header');
    const filteredChartsKeys = Object.keys(groupedCharts).filter(
        (key) => !key.toLocaleLowerCase().includes('model architecture')
    );

    return filteredChartsKeys.map((header) => {
        const chartsOfHeader = groupedCharts[header];

        if (chartsOfHeader.length !== 1 && chartsOfHeader.every(isBarChartType)) {
            return {
                header,
                key: idMatchingFormat(header),
                type: 'group',
                values: chartsOfHeader.map((statistic) => getValueForBar(statistic)),
            };
        }

        const objStatistic = chartsOfHeader[0];

        return getStatisticEntity(objStatistic);
    });
};

const mockedDatasetStatisticsDTO: DatasetStatisticsDTO = {
    images: 8,
    videos: 6,
    annotated_frames: 2,
    annotated_images: 5,
    annotated_videos: 4,
    objects_per_label: [
        {
            id: '1',
            color: '#b100ffff',
            name: 'circle',
            value: 2,
        },
        {
            id: '2',
            color: '#00147fff',
            name: 'square',
            value: 4,
        },
        {
            id: '3',
            color: '#00fffaff',
            name: 'rectangle',
            value: 1,
        },
        {
            id: '4',
            color: '#2a2b2eff',
            name: 'Empty torch_segmentation torch_segmentation',
            value: 0,
        },
    ],
    object_size_distribution_per_label: [
        {
            cluster_center: [402, 276],
            cluster_width_height: [304, 277],
            color: '#edb200ff',
            id: '619b97d3f19eee235e66b8d8',
            name: 'testdetc',
            object_distribution_from_aspect_ratio: {
                balanced: 2,
                tall: 0,
                wide: 0,
            },
            size_distribution: [
                [554, 414],
                [250, 137],
            ],
            aspect_ratio_threshold_wide: 0.07,
            aspect_ratio_threshold_tall: 6.87,
        },
    ],
};

export const mockedDatasetStatistics = getDatasetStatisticsEntity(mockedDatasetStatisticsDTO);
export const mockedAllDatasetStatistics = getAllTaskDatasetStatisticsDTO({
    overview: {
        images: 8,
        videos: 6,
        annotated_frames: 2,
        annotated_images: 5,
        annotated_videos: 4,
    },
    tasks: [{ task_id: '123', ...mockedDatasetStatisticsDTO }],
});
