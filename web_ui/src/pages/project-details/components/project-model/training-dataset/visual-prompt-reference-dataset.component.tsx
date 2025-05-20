// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, View } from '@geti/ui';

import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';
import { SubsetBucket } from './subset-bucket/subset-bucket.component';
import { TrainingDatasetProps } from './training-dataset.interface';
import { Subset } from './utils';

export const VisualPromptReferenceDataset = ({
    revisionId,
    storageId,
    modelInformation,
    modelLabels,
    taskId,
    isActive,
}: TrainingDatasetProps): JSX.Element => {
    const projectIdentifier = useProjectIdentifier();

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
                {/* Unlike incremental models a visual prompt model only has a training set */}
                <SubsetBucket {...subsetsCommonProps} mediaPercentage={''} type={Subset.TRAINING} />
            </Flex>
        </View>
    );
};
