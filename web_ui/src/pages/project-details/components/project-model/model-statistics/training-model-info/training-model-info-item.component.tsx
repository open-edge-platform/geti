// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Flex, Text } from '@geti/ui';

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
