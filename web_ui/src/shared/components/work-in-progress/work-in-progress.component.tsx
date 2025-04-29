// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Heading, Text } from '@adobe/react-spectrum';

import { WorkInProgressIcon } from '../../../assets/images';

import classes from './work-in-progress.module.scss';

export const WorkInProgress = ({ description }: { description?: string }): JSX.Element => {
    return (
        <Flex direction='column' alignItems='center' justifyContent='center' height='100%'>
            <WorkInProgressIcon />
            <Heading level={1} UNSAFE_className={classes.heading}>
                Work in progress
            </Heading>
            <Text>{description ?? 'We are working hard to get this up and running'}</Text>
        </Flex>
    );
};
