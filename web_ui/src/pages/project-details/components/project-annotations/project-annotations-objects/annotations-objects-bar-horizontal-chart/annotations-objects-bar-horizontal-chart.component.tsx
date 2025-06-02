// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';
import { useNavigate } from 'react-router-dom';

import {
    AdvancedFilterOptions,
    SearchRuleField,
    SearchRuleOperator,
} from '../../../../../../core/media/media-filter.interface';
import { encodeFilterSearchParam } from '../../../../../../hooks/use-filter-search-param/use-filter-search-param.hook';
import { BarHorizontalChart } from '../../../../../../shared/components/charts/bar-horizontal-chart/bar-horizontal-chart.component';
import { ChartProps, Colors } from '../../../../../../shared/components/charts/chart.interface';
import { useDatasetIdentifier } from '../../../../../annotator/hooks/use-dataset-identifier.hook';

interface AnnotationObjectsBarHorizontalChartProps extends ChartProps {
    title: string;
    barSize?: number;
    yPadding?: {
        top?: number;
        bottom?: number;
    };
    colors: Colors[];
}

export const AnnotationObjectsBarHorizontalChart = ({
    title,
    data,
    barSize = 20,
    yPadding,
    colors,
}: AnnotationObjectsBarHorizontalChartProps): JSX.Element => {
    const navigate = useNavigate();
    const datasetIdentifier = useDatasetIdentifier();

    const handleCellClick = (labelId: string | undefined) => {
        if (!labelId) {
            // if there's no labelId, we don't navigate to the dataset
            return;
        }

        const search: AdvancedFilterOptions = {
            condition: 'and',
            rules: [
                {
                    field: SearchRuleField.LabelId,
                    id: `${datasetIdentifier.datasetId}-${labelId}`,
                    operator: SearchRuleOperator.In,
                    value: [labelId],
                },
            ],
        };
        const encodedFilters = encodeFilterSearchParam(search);
        const filter = `?filter=${encodedFilters.toString()}`;
        const route = `${paths.project.dataset.media(datasetIdentifier)}${filter}`;

        navigate(route);
    };

    return (
        <BarHorizontalChart
            title={title}
            data={data}
            barSize={barSize}
            yPadding={yPadding}
            colors={colors}
            allowDecimals={false}
            onCellClick={handleCellClick}
        />
    );
};
