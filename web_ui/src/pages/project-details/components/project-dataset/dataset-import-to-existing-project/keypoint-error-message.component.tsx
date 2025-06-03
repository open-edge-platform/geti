// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text } from '@geti/ui';
import { Alert } from '@geti/ui/icons';
import { isEmpty } from 'lodash-es';

import { Label } from '../../../../../core/labels/label.interface';
import { isNonEmptyArray } from '../../../../../shared/utils';
import {
    getDuplicates,
    KEYPOINT_ANNOTATION_WARNING,
    KEYPOINT_DUPLICATED_LABELS,
    KEYPOINT_MISSING_LABELS,
} from './utils';

export interface KeypointErrorProps {
    labelsMap: Record<string, string>;
    labels: Label[];
}

const concatNames = (labels: Label[]) => labels.map(({ name }) => name).join(', ');

export const KeypointErrorMessage = ({ labelsMap, labels }: KeypointErrorProps) => {
    const labelsMapValues = Object.values(labelsMap);
    const duplicatedValues = getDuplicates(labelsMapValues);

    const missingLabels = labels.filter((label) => !labelsMapValues.includes(label.id));
    const duplicatedLabels = labels.filter((label) => duplicatedValues.includes(label.id));

    if (isEmpty(missingLabels) && isEmpty(duplicatedLabels)) {
        return <></>;
    }

    return (
        <Flex gap={'size-100'} alignContent={'center'} height={'100%'} alignItems={'center'}>
            <Alert style={{ fill: 'var(--brand-coral-cobalt)' }} />
            <Flex direction={'column'} gap={'size-100'}>
                {isNonEmptyArray(duplicatedLabels) && (
                    <Text>
                        {KEYPOINT_DUPLICATED_LABELS} {concatNames(duplicatedLabels)}
                    </Text>
                )}
                {isNonEmptyArray(missingLabels) && (
                    <>
                        <Text>
                            {KEYPOINT_MISSING_LABELS} {concatNames(missingLabels)}
                        </Text>
                        <Text>{KEYPOINT_ANNOTATION_WARNING}</Text>
                    </>
                )}
            </Flex>
        </Flex>
    );
};
