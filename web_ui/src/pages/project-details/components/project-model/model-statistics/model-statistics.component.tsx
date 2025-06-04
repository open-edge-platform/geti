// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Fragment, useMemo, useRef } from 'react';

import { Content, Flex, Grid, Loading, useUnwrapDOMRef } from '@geti/ui';
import { HttpStatusCode } from 'axios';
import { isEmpty } from 'lodash-es';

import { useModelStatistics } from '../../../../../core/statistics/hooks/use-model-statistics.hook';
import { useModelIdentifier } from '../../../../../hooks/use-model-identifier/use-model-identifier.hook';
import { DownloadSvgButton } from './download-svg-button.component';
import { ModelStatisticsError } from './model-statistics-error/model-statistics-error.component';
import { ModelStatisticsNotFound } from './model-statistics-not-found/model-statistics-not-found.component';
import { TrainingModelInfo } from './training-model-info/training-model-info.component';
import { getModelStatisticPresentation, getModelStatistics } from './utils';

import classes from './model-statistics.module.scss';

export const ModelStatistics = (): JSX.Element => {
    const container = useRef(null);
    const unwrappedContainer = useUnwrapDOMRef(container);

    const modelIdentifier = useModelIdentifier();
    const { isLoading, data: modelStatisticsData = [], error } = useModelStatistics(modelIdentifier);

    const { trainingMetrics, trainingMetadata } = useMemo(
        () => getModelStatistics(modelStatisticsData),
        [modelStatisticsData]
    );

    if (error?.response?.status === HttpStatusCode.NotFound) {
        return <ModelStatisticsNotFound />;
    }

    if (isLoading) {
        return <Loading />;
    }

    if (isEmpty(modelStatisticsData)) {
        return <ModelStatisticsError />;
    }

    return (
        <Flex direction={'column'} minHeight={0} height={'100%'} ref={container} marginTop={'size-100'}>
            <Flex alignItems={'center'}>
                {!isEmpty(trainingMetadata) ? <TrainingModelInfo trainingMetadata={trainingMetadata} /> : <></>}
                <Content UNSAFE_className={classes.downloadAllGraphsContainer}>
                    <DownloadSvgButton
                        text={'Download all graphs'}
                        fileName={'Model metrics'}
                        container={unwrappedContainer}
                        graphBackgroundColor={'gray-100'}
                        UNSAFE_className={classes.downloadAllGraphs}
                    />
                </Content>
            </Flex>
            <Grid marginTop={'size-250'} autoRows={'45rem'} gap={'size-200'} UNSAFE_className={classes.gridStatistics}>
                {trainingMetrics.map((modelStatistics) => (
                    <div key={modelStatistics.key} aria-label={`${modelStatistics.header} chart`}>
                        {getModelStatisticPresentation(modelStatistics)}
                    </div>
                ))}
            </Grid>
        </Flex>
    );
};
