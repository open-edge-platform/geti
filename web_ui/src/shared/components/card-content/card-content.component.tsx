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

import { CSSProperties, ReactNode, useRef } from 'react';

import { Divider, Flex, Heading, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';
import { StyleProps } from '@react-types/shared';
import isEmpty from 'lodash/isEmpty';

import { Info } from '../../../assets/icons';
import { idMatchingFormat } from '../../../test-utils/id-utils';
import { ActionElement } from '../action-element/action-element.component';
import { DownloadGraphMenu } from '../download-graph-menu/download-graph-menu.component';
import { DownloadableData } from '../download-graph-menu/export-csv-utils';

interface CardContentProps extends StyleProps {
    children: ReactNode;
    title: string;
    gridArea?: string;
    styles?: CSSProperties;
    actions?: JSX.Element;
    isDownloadable?: boolean;
    titleActions?: ReactNode;
    downloadableData?: DownloadableData;
    tooltip?: string;
}

export const CardContent = ({
    styles,
    children,
    gridArea,
    title = 'Number of media',
    actions = <></>,
    titleActions,
    isDownloadable = false,
    downloadableData,
    tooltip,
    ...rest
}: CardContentProps): JSX.Element => {
    const id = idMatchingFormat(title);
    const container = useRef(null);

    return (
        <View
            borderRadius={'small'}
            backgroundColor={'gray-100'}
            gridArea={gridArea}
            padding={'size-200'}
            UNSAFE_style={{ boxSizing: 'border-box', ...styles }}
            ref={container}
            {...rest}
        >
            <Flex direction='column' height='100%'>
                <Flex justifyContent={'space-between'} alignItems='center' width={'100%'}>
                    <Flex alignItems={'center'} gap={titleActions ? 'size-200' : ''}>
                        <Heading level={6} marginY={0} id={`${gridArea ?? id}-id`} marginEnd={'size-100'}>
                            {title}
                        </Heading>

                        {!isEmpty(tooltip) && (
                            <TooltipTrigger placement={'bottom'}>
                                <ActionElement aria-label='label-relation' UNSAFE_style={{ display: 'flex' }}>
                                    <Info width={16} height={16} />
                                </ActionElement>
                                <Tooltip>{tooltip}</Tooltip>
                            </TooltipTrigger>
                        )}

                        {titleActions}
                    </Flex>

                    <Flex alignItems={'center'} justifyContent={'end'}>
                        {isDownloadable && (
                            <DownloadGraphMenu
                                ref={container}
                                fileName={title}
                                data={downloadableData}
                                tooltip={'Download graph'}
                                graphBackgroundColor={'gray-100'}
                            />
                        )}
                        {actions}
                    </Flex>
                </Flex>
                <Divider size='S' marginY={'size-200'} />
                <Flex
                    id={`${id}-content-id`}
                    flexBasis={'100%'}
                    flex={1}
                    direction={'column'}
                    justifyContent={'center'}
                    minHeight={0}
                >
                    <View height={'100%'}>{children}</View>
                </Flex>
            </Flex>
        </View>
    );
};
