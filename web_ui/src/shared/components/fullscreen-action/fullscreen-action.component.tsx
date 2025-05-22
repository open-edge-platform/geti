// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useRef } from 'react';

import {
    ActionButton,
    ButtonGroup,
    Content,
    Dialog,
    DialogTrigger,
    Divider,
    Heading,
    Tooltip,
    TooltipTrigger,
} from '@geti/ui';
import { Collapse, Expand } from '@geti/ui/icons';
import { isString } from 'lodash-es';

import { idMatchingFormat } from '../../../test-utils/id-utils';
import { DownloadGraphMenu } from '../download-graph-menu/download-graph-menu.component';
import { DownloadableData } from '../download-graph-menu/export-csv-utils';

import classes from './fullscreen-dialog.module.scss';

interface FullscreenActionProps {
    children: ReactNode;
    isDownloadable?: boolean;
    title: string | ReactNode;
    actionButton?: ReactNode;
    downloadableData?: DownloadableData;
}

export const FullscreenAction = ({
    children,
    title,
    downloadableData,
    actionButton,
    isDownloadable = false,
}: FullscreenActionProps): JSX.Element => {
    const container = useRef(null);
    const svgTitle = isString(title) ? title : 'Graph';

    return (
        <DialogTrigger type='fullscreenTakeover'>
            <TooltipTrigger placement={'bottom'}>
                <ActionButton
                    isQuiet
                    aria-label={`Open in fullscreen ${title}`}
                    id={`${idMatchingFormat(svgTitle)}-open-fullscreen`}
                >
                    <Expand />
                </ActionButton>
                <Tooltip>Fullscreen</Tooltip>
            </TooltipTrigger>

            {(close) => (
                <Dialog UNSAFE_className={classes.fullscreenDialog} aria-label={`${title} fullscreen`}>
                    <Heading UNSAFE_style={{ fontSize: 'var(--spectrum-global-dimension-font-size-200)' }}>
                        {title}
                    </Heading>

                    <Divider />

                    <ButtonGroup>
                        {isDownloadable && (
                            <DownloadGraphMenu
                                ref={container}
                                fileName={svgTitle}
                                data={downloadableData}
                                tooltip={'Download graph'}
                                graphBackgroundColor={'gray-100'}
                            />
                        )}

                        {actionButton}

                        <TooltipTrigger placement={'bottom'}>
                            <ActionButton isQuiet onPress={close} aria-label='Close fullscreen'>
                                <Collapse />
                            </ActionButton>
                            <Tooltip>Close fullscreen</Tooltip>
                        </TooltipTrigger>
                    </ButtonGroup>

                    <Content UNSAFE_style={{ overflow: 'hidden' }} ref={container}>
                        {children}
                    </Content>
                </Dialog>
            )}
        </DialogTrigger>
    );
};
