import { useNavigate } from 'react-router-dom';

import { SearchRuleField, SearchRuleOperator } from '../../../../../../core/media/media-filter.interface';
import { paths } from '../../../../../../core/services/routes';
import { encodeFilterSearchParam } from '../../../../../../hooks/use-filter-search-param/use-filter-search-param.hook';
import { BarHorizontalChart } from '../../../../../../shared/components/charts/bar-horizontal-chart/bar-horizontal-chart.component';
import { ChartProps, Colors } from '../../../../../../shared/components/charts/chart.interface';
import { useDatasetIdentifier } from '../../../../../annotator/hooks/use-dataset-identifier.hook';
import { useProject } from '../../../../providers/project-provider/project-provider.component';

interface AnnotationObjectsBarHorizontalChartProps extends ChartProps {
    barSize?: number;
    yPadding?: {
        top?: number;
        bottom?: number;
    };
    colors: Colors[];
}

export const AnnotationObjectsBarHorizontalChart = ({
    data,
    barSize = 20,
    yPadding,
    colors,
}: AnnotationObjectsBarHorizontalChartProps): JSX.Element => {
    const navigate = useNavigate();
    const datasetIdentifier = useDatasetIdentifier();
    const { project } = useProject();
    const title = 'Number of objects per label';

    const handleLabelClick = (labelName: string) => {
        const labelId = project.labels.find((label) => label.name === labelName)?.id;

        if (!labelId) {
            // if there's no labelId, we don't navigate to the dataset
            return;
        }

        const search = {
            condition: 'and',
            rules: [
                {
                    field: SearchRuleField.LabelId,
                    id: datasetIdentifier,
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
            handleLabelClick={handleLabelClick}
        />
    );
};
