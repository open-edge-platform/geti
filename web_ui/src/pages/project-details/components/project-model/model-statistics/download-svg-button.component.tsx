// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';
import { SpectrumActionButtonProps } from '@react-types/button';
import { BackgroundColorValue } from '@react-types/shared';

import { DownloadIcon } from '../../../../../assets/icons';
import { NOTIFICATION_TYPE } from '../../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../notification/notification.component';
import {
    DOWNLOADABLE_HTML_SELECTOR,
    DOWNLOADABLE_SVG_SELECTOR,
    downloadMultiplePages,
    ERROR_MESSAGE,
    getContainerElements,
    getVarColorToHex,
} from '../../../../../shared/components/download-graph-menu/export-svg-utils';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';

import classes from './download-svg-button.module.scss';

interface DownloadSvgButtonProps extends SpectrumActionButtonProps {
    text?: string;
    tooltip?: string;
    fileName: string;
    container: React.RefObject<HTMLElement>;
    graphBackgroundColor: BackgroundColorValue;
}

export const DownloadSvgButton = ({
    text = '',
    fileName,
    container,
    gridArea,
    marginStart,
    marginBottom,
    tooltip = text,
    graphBackgroundColor,
    ...props
}: DownloadSvgButtonProps) => {
    const { addNotification } = useNotification();
    const [isDownloading, setIsDownloading] = useState(false);
    const hexColor = getVarColorToHex(`--spectrum-global-color-${graphBackgroundColor}`);

    const onDownloadPdf = async () => {
        setIsDownloading(true);
        try {
            const svgs = getContainerElements<SVGSVGElement>(container.current, DOWNLOADABLE_SVG_SELECTOR);
            const htmls = getContainerElements<HTMLDivElement>(container.current, DOWNLOADABLE_HTML_SELECTOR);

            await downloadMultiplePages(fileName, svgs, htmls, hexColor);
        } catch (_e) {
            addNotification({ message: ERROR_MESSAGE, type: NOTIFICATION_TYPE.ERROR });
        } finally {
            setIsDownloading(false);
        }
    };

    return (
        <View
            gridArea={gridArea}
            marginStart={marginStart}
            marginBottom={marginBottom}
            UNSAFE_style={{ width: 'fit-content' }}
        >
            <TooltipTrigger placement={'bottom'}>
                <QuietActionButton
                    onPress={onDownloadPdf}
                    isDisabled={isDownloading}
                    {...props}
                    aria-label='download svg'
                    UNSAFE_className={classes.downloadAllGraphs}
                >
                    {text} <DownloadIcon />
                </QuietActionButton>
                <Tooltip>{tooltip}</Tooltip>
            </TooltipTrigger>
        </View>
    );
};
