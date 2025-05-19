// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Flex, Text } from '@geti/ui';

import classes from './empty-data.module.scss';

interface EmptyDataProps {
    title: string;
    text: string;
    beforeText?: ReactNode;
    afterText?: ReactNode;
}

export const EmptyData = ({ title, text, beforeText = null, afterText = null }: EmptyDataProps): JSX.Element => {
    return (
        <Flex justifyContent={'center'} alignItems={'center'} height={'100%'} id='empty-data-id'>
            <Flex direction={'column'} alignItems={'center'}>
                {beforeText}

                <Text marginTop={'size-150'} UNSAFE_className={classes.emptyData}>
                    {title}
                </Text>
                <Text>{text}</Text>

                {afterText}
            </Flex>
        </Flex>
    );
};
