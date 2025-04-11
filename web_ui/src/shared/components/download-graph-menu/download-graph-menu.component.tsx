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

import { forwardRef, RefObject, useState } from 'react';

import { useUnwrapDOMRef } from '@react-spectrum/utils';
import { BackgroundColorValue, DOMRefValue } from '@react-types/shared';

import { DownloadIcon } from '../../../assets/icons';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { idMatchingFormat } from '../../../test-utils/id-utils';
import { runWhenTruthy } from '../../utils';
import { MenuTriggerList } from '../menu-trigger-list/menu-trigger-list.component';
import {
    DownloadableData,
    downloadCSV,
    getFormattedArray,
    getFormattedBarChart,
    getFormattedLineChart,
    getFormattedMatrix,
    getFormattedText,
} from './export-csv-utils';
import {
    DOWNLOADABLE_HTML_SELECTOR,
    DOWNLOADABLE_SVG_SELECTOR,
    downloadMultiplePages,
    ERROR_MESSAGE,
    getContainerElements,
    getVarColorToHex,
} from './export-svg-utils';

interface DownloadGraphMenuProps {
    tooltip?: string;
    fileName: string;
    data?: DownloadableData;
    graphBackgroundColor: BackgroundColorValue;
}

const onFormatAndDownload = runWhenTruthy((downloadableData: DownloadableData, fileName: string): void => {
    if (downloadableData.type === 'text') {
        downloadCSV(fileName, getFormattedText(downloadableData));
    }

    if (downloadableData.type === 'matrix') {
        downloadCSV(fileName, getFormattedMatrix(downloadableData));
    }

    if (downloadableData.type === 'lineChart') {
        downloadCSV(fileName, getFormattedLineChart(downloadableData));
    }

    if (downloadableData.type === 'barChart') {
        downloadCSV(fileName, getFormattedBarChart(downloadableData));
    }

    if (downloadableData.type === 'default') {
        downloadCSV(fileName, getFormattedArray(downloadableData));
    }
});

export const DownloadGraphMenu = forwardRef<HTMLDivElement, DownloadGraphMenuProps>(
    ({ data, tooltip, fileName, graphBackgroundColor }, ref): JSX.Element => {
        const { addNotification } = useNotification();
        const [isDownloading, setIsDownloading] = useState(false);
        const container = ref as RefObject<DOMRefValue<HTMLDivElement>>;
        const unwrappedContainer = useUnwrapDOMRef(container);
        const hexColor = getVarColorToHex(`--spectrum-global-color-${graphBackgroundColor}`);

        const onDownloadPdf = async () => {
            setIsDownloading(true);

            try {
                const svgs = getContainerElements<SVGSVGElement>(unwrappedContainer.current, DOWNLOADABLE_SVG_SELECTOR);
                const htmls = getContainerElements<HTMLDivElement>(
                    unwrappedContainer.current,
                    DOWNLOADABLE_HTML_SELECTOR
                );

                await downloadMultiplePages(fileName, svgs, htmls, hexColor);
            } catch (_e) {
                addNotification({ message: ERROR_MESSAGE, type: NOTIFICATION_TYPE.ERROR });
            } finally {
                setIsDownloading(false);
            }
        };

        const onDownloadCSV = async () => {
            setIsDownloading(true);

            try {
                onFormatAndDownload(data, fileName);
            } catch (_e) {
                addNotification({ message: ERROR_MESSAGE, type: NOTIFICATION_TYPE.ERROR });
            } finally {
                setIsDownloading(false);
            }
        };

        const menuOptions: [string, () => void][] = [
            ['PDF', onDownloadPdf],
            ['CSV', onDownloadCSV],
        ];

        return (
            <MenuTriggerList
                id={`${idMatchingFormat(fileName)}-download-action-menu`}
                ariaLabel={`Download menu`}
                title={tooltip}
                options={menuOptions}
                icon={<DownloadIcon />}
                isDisabled={isDownloading}
            />
        );
    }
);
