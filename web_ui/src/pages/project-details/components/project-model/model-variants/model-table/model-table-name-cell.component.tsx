// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Text } from '@adobe/react-spectrum';

import { OptimizedModel, TrainedModel } from '../../../../../../core/models/optimized-models.interface';
import { TruncatedText } from '../../../../../../shared/components/truncated-text/truncated-text.component';
import { isNonEmptyString } from '../../../../../../shared/utils';
import { isOptimizationType, ModelTableColumnKeys } from '../utils';

interface ModelTableNameCellProps {
    row: OptimizedModel | TrainedModel;
    defaultDescription?: string;
}

export const ModelTableNameCell = ({ row, defaultDescription }: ModelTableNameCellProps) => {
    const hasExplainableAI = 'hasExplainableAI' in row ? row.hasExplainableAI : false;
    const description = isOptimizationType(row, 'POT') ? 'Post-training optimization' : undefined;
    const hasDescription = isNonEmptyString(description) || isNonEmptyString(defaultDescription);

    return (
        <Flex direction={'column'}>
            <TruncatedText id={`${row.id}-modelName`}>
                {`${row[ModelTableColumnKeys.MODEL_NAME]} ${hasExplainableAI ? '(Explanation included)' : ''}`}
            </TruncatedText>

            {hasDescription && (
                <Text
                    UNSAFE_style={{
                        color: 'var(--spectrum-global-color-gray-700)',
                        fontSize: 'var(--spectrum-global-dimension-font-size-50)',
                    }}
                    id={`${row.id}-description-id`}
                >
                    {description ?? defaultDescription} {hasExplainableAI ? '(Explanation included)' : ''}
                </Text>
            )}
        </Flex>
    );
};
