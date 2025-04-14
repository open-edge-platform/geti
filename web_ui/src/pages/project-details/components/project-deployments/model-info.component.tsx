// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text, View } from '@adobe/react-spectrum';

import { OptimizedModel } from '../../../../core/models/optimized-models.interface';
import { useFormatModelAccuracy } from '../../../../shared/hooks/use-format-model-accuracy.hook';

import classes from './project-deployments.module.scss';

interface ModelInfoProps {
    optimizedModel: OptimizedModel | undefined;
}

export const ModelInfo = ({ optimizedModel }: ModelInfoProps) => {
    const accuracy = useFormatModelAccuracy(optimizedModel?.accuracy);

    return (
        <Flex UNSAFE_className={classes.modelInfo} id={'model-info-container-id'}>
            <View UNSAFE_className={classes.infoItem}>
                <Text UNSAFE_className={classes.title}>Score</Text>
                <Text UNSAFE_className={classes.description} id={'model-info-accuracy-id'}>
                    {accuracy}
                </Text>
            </View>

            <View UNSAFE_className={classes.infoItem}>
                <Text UNSAFE_className={classes.title}>Precision</Text>
                <Text UNSAFE_className={classes.description} id={'model-info-precision-id'}>
                    {optimizedModel?.precision ? optimizedModel.precision[0] : '-'}
                </Text>
            </View>
        </Flex>
    );
};
