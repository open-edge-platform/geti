// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Media } from '@/api/types';
import { Content, ContextualHelp, Divider, Text } from '@geti-ui/ui';

import { isVideo } from '../../../../shared/media-item-utils';
import { formatBytes } from '../../../../shared/util';

import classes from './media-item-contextual-help.module.scss';

type MediaItemContextualHelpProps = {
    item: Media;
};

export const MediaItemContextualHelp = ({ item }: MediaItemContextualHelpProps) => {
    return (
        <>
            <ContextualHelp
                variant='info'
                UNSAFE_className={classes.videoIndicatorDetails}
                aria-label='Media information'
            >
                <Content>
                    <Text>Format: {item.format}</Text>
                    <br />
                    <Text>Width: {item.width} px</Text>
                    <br />
                    <Text>Height: {item.height} px</Text>
                    <br />
                    <Text>Size: {formatBytes(item.size)}</Text>

                    {isVideo(item) && (
                        <>
                            <br />
                            <br />
                            <Text>Number of annotated frames: {item.annotated_frame_count}</Text>
                            <br />
                            <Text>Total frames: {item.frame_count}</Text>
                        </>
                    )}
                </Content>
            </ContextualHelp>

            <Divider orientation={'vertical'} size={'S'} />
        </>
    );
};
