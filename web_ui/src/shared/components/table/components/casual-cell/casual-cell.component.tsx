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

import { ReactNode } from 'react';

import { Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { formatUtcToLocal } from '../../../../utils';
import { ActionElement } from '../../../action-element/action-element.component';
import { TruncatedText } from '../../../truncated-text/truncated-text.component';
import { TableCellProps } from '../../table.interface';

interface CasualCellProps extends TableCellProps {
    tooltip?: ReactNode;
}

export const CasualCell = ({ rowData, cellData, dataKey, tooltip, styles }: CasualCellProps): JSX.Element => {
    let id = dataKey;

    if (rowData.id) {
        id = `${rowData.id}-${dataKey}`;
    } else if (rowData.modelName) {
        id = `${idMatchingFormat(rowData.modelName)}-${dataKey}`;
    }

    if (dataKey === 'precision') {
        if (cellData && cellData.length) {
            cellData = cellData[0];
        }
    } else if (dataKey === 'expiresAt' || dataKey === 'createdAt') {
        cellData = formatUtcToLocal(rowData[dataKey], 'DD MMM YYYY');
    }

    return (
        <TooltipTrigger placement={'bottom left'}>
            <ActionElement>
                <TruncatedText id={id} data-testid={id} UNSAFE_style={styles}>
                    {cellData}
                </TruncatedText>
            </ActionElement>
            <Tooltip>{tooltip ?? cellData}</Tooltip>
        </TooltipTrigger>
    );
};
