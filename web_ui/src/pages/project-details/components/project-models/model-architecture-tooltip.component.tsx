// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Divider, Text, View } from '@adobe/react-spectrum';

import { DeprecatedTag } from './models-container/model-card/deprecated-model-tag.component';
import { ObsoleteTag } from './models-container/model-card/obsolete-model-tag.component';

const DEPRECATED_MODEL_EXPLANATION =
    `This architecture is no longer actively developed. ` +
    `In the future you will no longer be able to train new model versions on this architecture.`;
const OBSOLETE_MODEL_EXPLANATION =
    'The architecture is no longer supported, which means it cannot be used for training new models, ' +
    'but previously trained models can be still evaluated, optimized, and deployed.';

interface ModelArchitectureTooltipTextProps {
    isDeprecated?: boolean;
    isObsolete?: boolean;
    description: string;
}

export const ModelArchitectureTooltipText = ({
    isDeprecated,
    isObsolete,
    description,
}: ModelArchitectureTooltipTextProps) => {
    return (
        <View>
            <Text>{description}</Text>
            {isDeprecated && (
                <>
                    <Divider marginY={'size-150'} height={'size-10'} />
                    <DeprecatedTag id={''} />
                    <Text marginTop={'size-50'} UNSAFE_style={{ display: 'block' }}>
                        {DEPRECATED_MODEL_EXPLANATION}
                    </Text>
                </>
            )}
            {isObsolete && (
                <>
                    <Divider marginY={'size-150'} height={'size-10'} />
                    <ObsoleteTag id={''} />
                    <Text marginTop={'size-50'} UNSAFE_style={{ display: 'block' }}>
                        {OBSOLETE_MODEL_EXPLANATION}
                    </Text>
                </>
            )}
        </View>
    );
};
