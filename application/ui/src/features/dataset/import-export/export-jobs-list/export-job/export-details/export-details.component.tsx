// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { ExportDatasetMetadata } from '@/api/types';
import { dimensionValue, Divider, Flex, Grid, Text } from '@geti-ui/ui';
import { isEmpty, isNil } from 'lodash-es';

import { useDatasetViewsQuery } from '../../../../../../features/dataset/gallery/toolbar/dataset-view-selector/api/use-dataset-views';
import { useProject } from '../../../../../../hooks/api/project.hook';

type ExportJobDetailsProps = {
    datasetName?: string;
    metadata: ExportDatasetMetadata;
};

const isGetiFormat = (format?: string | null) => format?.toLowerCase() === 'geti';

export const ExportJobDetails = ({ datasetName, metadata }: ExportJobDetailsProps) => {
    const { data: selectedProject } = useProject();
    const { data: viewsData } = useDatasetViewsQuery();

    const projectLabels = selectedProject.task.labels ?? [];
    const exportLabelsNames = metadata.filters.labels ?? [];

    const projectLabelsNames = projectLabels.map((label) => label.name);
    const selectedLabels = exportLabelsNames.filter((name) => projectLabelsNames.includes(name));

    const labelsList = isEmpty(selectedLabels) ? projectLabelsNames : selectedLabels;

    const viewName = metadata.dataset_view_id
        ? (viewsData?.find((v: { id: string; name: string }) => v.id === metadata.dataset_view_id)?.name ??
          'Deleted view')
        : undefined;

    return (
        <Flex direction={'column'}>
            <Text UNSAFE_style={{ fontWeight: 500, fontSize: dimensionValue('size-225') }}>
                Export {isNil(datasetName) ? 'dataset' : datasetName}
            </Text>

            <Grid
                marginTop={'size-200'}
                alignItems={'center'}
                gap='size-125'
                columns={[...'auto,1px'.repeat(viewName ? 3 : 2).split(','), '1fr']}
            >
                {viewName && (
                    <>
                        <Text>View: {viewName}</Text>
                        <Divider orientation='vertical' size='S' />
                    </>
                )}
                <Text>
                    Format:{' '}
                    <Text
                        UNSAFE_style={{
                            textTransform: isGetiFormat(metadata.export_format) ? 'capitalize' : 'uppercase',
                        }}
                    >
                        {metadata.export_format}
                    </Text>{' '}
                </Text>

                <Divider orientation='vertical' size='S' />

                <Text>Media: {metadata.filters.include_unannotated ? 'All media' : 'Only media with annotations'}</Text>

                <Divider orientation='vertical' size='S' />

                <Text UNSAFE_style={{ overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>
                    Labels: {labelsList.join(', ')}
                </Text>
            </Grid>
        </Flex>
    );
};
