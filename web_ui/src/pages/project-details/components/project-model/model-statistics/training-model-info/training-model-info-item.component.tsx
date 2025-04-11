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

import { ReactNode } from 'react';

import { Flex, Text } from '@adobe/react-spectrum';

import classes from './training-model-info-item.module.scss';

interface TrainingDateProps {
    id: string;
    value: string;
    header: string;
    subText?: ReactNode;
}

export const TrainingModelInfoItem = ({ value, header, subText, id }: TrainingDateProps): JSX.Element => {
    return (
        <Flex direction={'column'} gap={'size-60'} data-testid={id}>
            {subText ? (
                <>
                    <Text UNSAFE_className={classes.trainingMetadataLabel}>{header}</Text>
                    <Flex gap={'size-100'} alignItems={'center'}>
                        <Text UNSAFE_className={classes.trainingMetadataValue}>{value}</Text>
                        {subText}
                    </Flex>
                </>
            ) : (
                <>
                    <Text UNSAFE_className={classes.trainingMetadataLabel}>{header}</Text>
                    <Text UNSAFE_className={classes.trainingMetadataValue}>{value}</Text>
                </>
            )}
        </Flex>
    );
};
