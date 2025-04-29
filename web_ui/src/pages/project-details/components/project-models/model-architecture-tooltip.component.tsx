// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
