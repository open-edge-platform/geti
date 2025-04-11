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
