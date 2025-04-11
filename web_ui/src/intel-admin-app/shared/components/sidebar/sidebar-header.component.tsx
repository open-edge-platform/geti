// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FC } from 'react';

import { Flex, View } from '@adobe/react-spectrum';

import { PhotoPlaceholder } from '../../../../shared/components/photo-placeholder/photo-placeholder.component';
import { Skeleton } from '../../../../shared/components/skeleton/skeleton.component';
import { TruncatedTextWithTooltip } from '../../../../shared/components/truncated-text/truncated-text.component';

import classes from './sidebar.module.scss';

interface SidebarHeaderProps {
    name: string | undefined;
    email?: string;
}

export const SidebarHeader: FC<SidebarHeaderProps> = ({ name, email }) => {
    return (
        <View paddingStart={'size-400'} paddingEnd={'size-200'} paddingY={'size-450'}>
            <Flex flex={1} gap={'size-200'} alignItems={'center'} height={'100%'}>
                {name ? (
                    <>
                        <PhotoPlaceholder name={name} email={email ?? name} width={'size-500'} height={'size-500'} />
                        <TruncatedTextWithTooltip UNSAFE_className={classes.sidebarHeaderText}>
                            {name}
                        </TruncatedTextWithTooltip>
                    </>
                ) : (
                    <Flex alignItems={'center'} gap={'size-400'}>
                        <Skeleton
                            width={'size-500'}
                            height={'size-500'}
                            UNSAFE_className={classes.sidebarHeaderSkeleton}
                            isCircle
                        />
                        <Skeleton
                            width={'size-2000'}
                            height={'size-300'}
                            UNSAFE_className={classes.sidebarHeaderSkeleton}
                        />
                    </Flex>
                )}
            </Flex>
        </View>
    );
};
