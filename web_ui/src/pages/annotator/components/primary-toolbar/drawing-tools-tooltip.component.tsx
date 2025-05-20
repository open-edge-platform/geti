// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex, Heading, IllustratedMessage, Text, View } from '@geti/ui';
import { Link } from 'react-router-dom';

import { useDocsUrl } from '../../../../hooks/use-docs-url/use-docs-url.hook';
import { ToolTooltipProps } from '../../tools/tools.interface';
import { Hotkey } from './hotkey/hotkey.component';

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
