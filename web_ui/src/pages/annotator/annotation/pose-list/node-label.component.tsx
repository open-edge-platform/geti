// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Text, View } from '@adobe/react-spectrum';
import { useNumberFormatter } from 'react-aria';

import { AiIcon } from '../../../../assets/icons';
import { AnnotationLabel } from '../../../../core/annotations/annotation.interface';
import { KeypointNode } from '../../../../core/annotations/shapes.interface';
import { isPrediction } from '../../../../core/labels/utils';
import { TruncatedTextWithTooltip } from '../../../../shared/components/truncated-text/truncated-text.component';

interface NodeLabelProps {
    point: KeypointNode;
}

export const NodeLabel = ({ point }: NodeLabelProps) => {
    const annotationLabel = point.label as AnnotationLabel;
    const formatter = useNumberFormatter({ style: 'percent', minimumFractionDigits: 0, maximumFractionDigits: 0 });

    if (!isPrediction(annotationLabel)) {
        return point.label.name;
    }

    return (
        <Flex
            gap={'size-65'}
            alignItems={'center'}
            maxWidth={'size-3000'}
            data-testid={`prediction label container`}
            UNSAFE_style={{
                padding: '0px var(--spectrum-global-dimension-size-50)',
                background: 'var(--spectrum-global-color-gray-75)',
            }}
        >
            <View>
                <AiIcon width={16} aria-label={'prediction icon'} />
            </View>

            <TruncatedTextWithTooltip>{point.label.name}</TruncatedTextWithTooltip>

            <Text>({formatter.format(annotationLabel.score as number)})</Text>
        </Flex>
    );
};
