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

import { CSSProperties } from 'react';

import { Divider, Flex, View } from '@adobe/react-spectrum';

import { Skeleton } from '../../skeleton/skeleton.component';

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
