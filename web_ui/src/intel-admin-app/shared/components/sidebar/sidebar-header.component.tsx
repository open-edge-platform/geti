// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Flex, View } from '@adobe/react-spectrum';
import { PhotoPlaceholder } from '@shared/components/photo-placeholder/photo-placeholder.component';
import { Skeleton } from '@shared/components/skeleton/skeleton.component';
import { TruncatedTextWithTooltip } from '@shared/components/truncated-text/truncated-text.component';

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
