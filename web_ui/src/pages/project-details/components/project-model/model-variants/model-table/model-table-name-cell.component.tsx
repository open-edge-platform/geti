// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
