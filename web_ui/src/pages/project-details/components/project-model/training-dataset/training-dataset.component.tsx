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

import { Flex, View } from '@adobe/react-spectrum';
import { useNumberFormatter } from 'react-aria';

import { useTrainingDatasetRevisionData } from '../../../../../core/datasets/hooks/use-training-dataset.hook';
import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';
import { Loading } from '../../../../../shared/components/loading/loading.component';
import { SubsetBucket } from './subset-bucket/subset-bucket.component';
import { TrainingDatasetProps } from './training-dataset.interface';
import { Subset } from './utils';

export const TrainingDataset = ({
    revisionId,
    storageId,
    modelInformation,
    modelLabels,
    taskId,
    isActive,
}: TrainingDatasetProps): JSX.Element => {
    const projectIdentifier = useProjectIdentifier();
    const { data, isSuccess, isLoading } = useTrainingDatasetRevisionData(projectIdentifier, storageId, revisionId);
    const formatter = useNumberFormatter({ style: 'percent', maximumFractionDigits: 0 });

    if (isLoading) {
        return <Loading size={'M'} />;
    }

    if (isSuccess) {
        const { trainingSubset, validationSubset, testingSubset } = data;
        const numberOfMedia = trainingSubset + validationSubset + testingSubset;

        const trainingSubsetPercentage = formatter.format(trainingSubset / numberOfMedia);
        const validationSubsetPercentage = formatter.format(validationSubset / numberOfMedia);
        const testingSubsetPercentage = formatter.format(testingSubset / numberOfMedia);

        const subsetsCommonProps = {
            projectIdentifier,
            storageId,
            revisionId,
            modelInformation,
            modelLabels,
            taskId,
            isActive,
        };

        return (
            <View
                id={'training-subsets-content'}
                padding={'size-200'}
                borderRadius={'regular'}
                backgroundColor={'gray-75'}
                data-testid={'training-subsets-content'}
                UNSAFE_style={{
                    height: 'calc(100% - var(--spectrum-global-dimension-size-600))',
                    flex: '1 1 auto',
                    display: 'flex',
                }}
            >
                <Flex gap={'size-150'} height={'100%'} width={'100%'}>
                    <SubsetBucket
                        {...subsetsCommonProps}
                        mediaPercentage={trainingSubsetPercentage}
                        type={Subset.TRAINING}
                    />

                    <SubsetBucket
                        {...subsetsCommonProps}
                        mediaPercentage={validationSubsetPercentage}
                        type={Subset.VALIDATION}
                    />

                    <SubsetBucket
                        {...subsetsCommonProps}
                        mediaPercentage={testingSubsetPercentage}
                        type={Subset.TESTING}
                    />
                </Flex>
            </View>
        );
    }

    return <></>;
};
