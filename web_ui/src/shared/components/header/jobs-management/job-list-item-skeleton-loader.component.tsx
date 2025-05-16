// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

import { Divider, Flex, View } from '@adobe/react-spectrum';
import { Skeleton } from '@geti/ui';

import classes from './job-list-item-skeleton-loader.module.scss';

export const JobListItemSkeletonLoader = ({
    itemCount = 3,
    style,
}: {
    itemCount: number;
    style?: CSSProperties;
}): JSX.Element => {
    return (
        <div data-testid='job-item-loader-list' role='progressbar' className={classes.skeletonContainer} style={style}>
            {[...Array(itemCount)].map((_elem, index) => (
                <Flex
                    UNSAFE_className={classes.wrapper}
                    data-testid={`job-item-loader-${index}`}
                    key={`job-item-loader-${index}`}
                >
                    <View UNSAFE_className={classes.jobInfo} margin={'size-200'}>
                        <Skeleton height={'size-250'} width={'10%'}></Skeleton>
                        <Flex marginTop={'size-200'}>
                            <Skeleton height={'size-200'} width={'14%'}></Skeleton>
                            <Skeleton height={'size-200'} marginX={'size-500'} width={'14%'}></Skeleton>
                            <Skeleton height={'size-200'} marginX={'size-500'} width={'14%'}></Skeleton>
                            <Skeleton height={'size-200'} width={'14%'} marginStart={'auto'}></Skeleton>
                        </Flex>
                        <Divider UNSAFE_className={classes.divider} height={'size-10'} marginY={'size-75'} />
                        <Skeleton height={'size-250'}></Skeleton>
                    </View>
                </Flex>
            ))}
        </div>
    );
};
