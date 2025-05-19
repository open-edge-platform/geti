// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

import { Divider, Flex, Skeleton, View } from '@geti/ui';

import classes from './skeleton-loader.module.scss';

export const ProjectListItemSkeletonLoader = ({
    itemCount = 3,
    style,
}: {
    itemCount: number;
    style?: CSSProperties;
}): JSX.Element => {
    return (
        <div
            data-testid='project-item-loader-list'
            role='progressbar'
            className={classes.skeletonContainer}
            style={style}
        >
            {[...Array(itemCount)].map((_elem, index) => (
                <Flex
                    UNSAFE_className={classes.wrapper}
                    data-testid={`project-item-loader-${index}`}
                    key={`project-item-loader-${index}`}
                >
                    <Skeleton width={'size-3600'} height={'100%'} flexGrow={1} flexShrink={0}></Skeleton>
                    <View UNSAFE_className={classes.projectInfo} margin={'size-200'}>
                        <Skeleton height={'size-350'} marginBottom={'size-100'}></Skeleton>
                        <Skeleton height={'size-250'} width={'30%'}></Skeleton>
                        <Divider
                            UNSAFE_className={classes.divider}
                            height={'size-10'}
                            marginTop='size-150'
                            marginBottom='size-150'
                        />
                        <Skeleton height={'size-250'} width={'80%'}></Skeleton>
                    </View>
                </Flex>
            ))}
        </div>
    );
};
