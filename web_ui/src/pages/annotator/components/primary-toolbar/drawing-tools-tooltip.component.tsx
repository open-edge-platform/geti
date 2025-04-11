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

import { Flex, Heading, IllustratedMessage, Text, View } from '@adobe/react-spectrum';
import { Link } from 'react-router-dom';

import { useDocsUrl } from '../../../../hooks/use-docs-url/use-docs-url.hook';
import { Divider } from '../../../../shared/components/divider/divider.component';
import { Hotkey } from '../../../../shared/components/hotkey/hotkey.component';
import { ToolTooltipProps } from '../../tools/tools.interface';

import classes from './primaryToolBar.module.scss';

interface DrawingToolsTooltipProps extends ToolTooltipProps {
    hotkey?: string;
}

export const DrawingToolsTooltip = ({
    title,
    description,
    url,
    img,
    hotkey,
}: DrawingToolsTooltipProps): JSX.Element => {
    const docsUrl = useDocsUrl();

    return (
        <IllustratedMessage>
            <img className={classes.drawingToolsTooltipsImg} src={img} alt={title} />
            <View UNSAFE_className={classes.drawingToolsTooltipsContent}>
                <Flex alignItems={'center'} justifyContent={'space-between'} order={2}>
                    <Heading UNSAFE_className={classes.drawingToolsTooltipsTitle}>{title}</Heading>
                    {hotkey !== undefined && <Hotkey hotkey={hotkey} />}
                </Flex>
                <Text UNSAFE_className={classes.drawingToolsTooltipsDescription}>{description}</Text>
                <Divider size='S' marginTop={'size-200'} marginBottom={'size-200'} />

                <Link
                    className={classes.learnMore}
                    to={`${docsUrl}${url}`}
                    target={'_blank'}
                    rel={'noopener noreferrer'}
                >
                    Learn more
                </Link>
            </View>
        </IllustratedMessage>
    );
};
