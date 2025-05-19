// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { PressableElement, Tooltip, TooltipTrigger } from '@geti/ui';

import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { formatUtcToLocal } from '../../../../utils';
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
            <PressableElement>
                <TruncatedText id={id} data-testid={id} UNSAFE_style={styles}>
                    {cellData}
                </TruncatedText>
            </PressableElement>
            <Tooltip>{tooltip ?? cellData}</Tooltip>
        </TooltipTrigger>
    );
};
