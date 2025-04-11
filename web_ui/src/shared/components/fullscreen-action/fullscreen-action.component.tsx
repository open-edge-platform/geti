// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ReactNode, useRef } from 'react';

import { ButtonGroup, Content, Dialog, DialogTrigger, Divider, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { Heading } from '@react-spectrum/text';
import isString from 'lodash/isString';

import { Collapse, Expand } from '../../../assets/icons';
import { idMatchingFormat } from '../../../test-utils/id-utils';
import { DownloadGraphMenu } from '../download-graph-menu/download-graph-menu.component';
import { DownloadableData } from '../download-graph-menu/export-csv-utils';
import { QuietActionButton } from '../quiet-button/quiet-action-button.component';

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
                <QuietActionButton
                    aria-label={`Open in fullscreen ${title}`}
                    id={`${idMatchingFormat(svgTitle)}-open-fullscreen`}
                >
                    <Expand />
                </QuietActionButton>
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
                            <QuietActionButton onPress={close} aria-label='Close fullscreen'>
                                <Collapse />
                            </QuietActionButton>
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
