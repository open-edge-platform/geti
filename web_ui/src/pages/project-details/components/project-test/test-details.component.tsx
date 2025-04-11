// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useState } from 'react';

import { Flex, Grid, Text } from '@adobe/react-spectrum';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { isAnomalyDomain, isDetectionDomain, isSegmentationDomain } from '../../../../core/projects/domains';
import { TASK_TYPE } from '../../../../core/projects/dtos/task.interface';
import { getDomain } from '../../../../core/projects/project.interface';
import { JobInfoStatus } from '../../../../core/tests/dtos/tests.interface';
import { Test } from '../../../../core/tests/tests.interface';
import { CardContent } from '../../../../shared/components/card-content/card-content.component';
import { useProject } from '../../providers/project-provider/project-provider.component';
import { getVersionWithDateText } from '../project-model/utils';
import { AccuracyHalfDonutChart } from '../project-models/models-container/model-card/accuracy-container/accuracy-half-donut-chart';
import { NoTestResults } from './no-test-results.component';
import { TestDetailsCard } from './test-details-card.component';
import { TestMediaContainer } from './test-media-container.component';
import { THRESHOLD_LABEL_TOOLTIP, THRESHOLD_TOOLTIP } from './utils';

interface TestDetailsProps {
    test: Test;
}

const hasTestResults = (test: Test) => {
    return test.jobInfo.status === JobInfoStatus.DONE && test.datasetsInfo.every(({ isDeleted }) => !isDeleted);
};

const getThresholdTooltip = (labelName: string) => {
    if (labelName === 'All labels') {
        return THRESHOLD_TOOLTIP;
    }

    return THRESHOLD_LABEL_TOOLTIP(labelName);
};

const TEST_GRID = ['details model-accuracy', 'media media'];

export const TestDetails = ({ test }: TestDetailsProps): JSX.Element => {
    const [selectedLabel, setSelectedLabel] = useState({ id: 'null', name: 'All labels' });
    const { modelInfo, datasetsInfo, creationTime, testName, scoreDescription, scores } = test;
    const {
        groupName,
        modelTemplateName,
        version,
        numberOfLabels,
        creationDate: modelCreationDate,
        taskType,
    } = modelInfo;
    const { datasetName, numberOfFrames, numberOfImages } = datasetsInfo[0];

    const { isSingleDomainProject } = useProject();

    const shouldShowGlobalLocalScore =
        isSingleDomainProject(isAnomalyDomain) &&
        (isSingleDomainProject(isDetectionDomain) || isSingleDomainProject(isSegmentationDomain));

    const score = scores.find(({ labelId }) => String(labelId) === selectedLabel.id)?.value;

    const jobWasCompleted = test.jobInfo.status === JobInfoStatus.DONE;

    return (
        <Grid
            areas={TEST_GRID}
            columns={jobWasCompleted ? ['3fr', '1fr'] : ['1fr']}
            rows={['max-content', '1fr']}
            gap={'size-200'}
            height={'100%'}
        >
            <TestDetailsCard
                version={version}
                creationDate={creationTime}
                modelName={`${modelTemplateName} (${groupName})`}
                testingSetName={datasetName}
                numberOfLabels={numberOfLabels}
                numberOfImages={numberOfImages}
                numberOfFrames={numberOfFrames}
                taskName={getDomain(taskType.toLowerCase() as TASK_TYPE) as DOMAIN}
            />
            {jobWasCompleted ? (
                <CardContent
                    title={'Model score'}
                    gridArea={'model-accuracy'}
                    tooltip={getThresholdTooltip(selectedLabel.name)}
                >
                    <Flex
                        height={'100%'}
                        alignItems={'center'}
                        justifyContent={'center'}
                        direction={'column'}
                        gap={'size-100'}
                    >
                        {score !== undefined ? (
                            <>
                                <AccuracyHalfDonutChart
                                    id={'test-model-accuracy'}
                                    ariaLabel={`${testName} model score`}
                                    value={Number(score)}
                                    size={'XL'}
                                />

                                {shouldShowGlobalLocalScore && <Text>{scoreDescription}</Text>}
                            </>
                        ) : (
                            <Text id={'test-model-accuracy'} data-testid={'test-model-accuracy'}>
                                N/A
                            </Text>
                        )}
                    </Flex>
                </CardContent>
            ) : (
                <></>
            )}

            {hasTestResults(test) ? (
                <TestMediaContainer
                    test={test}
                    taskType={taskType}
                    selectedLabelId={selectedLabel.id}
                    modelInfo={`${modelTemplateName} @ ${groupName} - ${getVersionWithDateText(
                        version,
                        modelCreationDate
                    )}`}
                    onLabelChange={setSelectedLabel}
                />
            ) : (
                <NoTestResults test={test} />
            )}
        </Grid>
    );
};
