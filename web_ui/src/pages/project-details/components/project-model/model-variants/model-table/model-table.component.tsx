// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Column, Flex, Heading, Row, TableBody, TableHeader, TableView } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

import { OptimizedModel, TrainedModel } from '../../../../../../core/models/optimized-models.interface';
import { isNonEmptyString } from '../../../../../../shared/utils';
import { ModelTableProps } from './model-table.interface';

export const ModelTable = ({
    data: rowData,
    columns,
    emptyModelMessage = '',
    ...tableStyles
}: ModelTableProps<OptimizedModel | TrainedModel> & {
    emptyModelMessage?: string;
}): JSX.Element => {
    if (isEmpty(rowData) && isEmpty(emptyModelMessage)) {
        return <></>;
    }

    if (isEmpty(rowData) && isNonEmptyString(emptyModelMessage)) {
        return (
            <Flex>
                <Heading level={3}>{emptyModelMessage}</Heading>
            </Flex>
        );
    }

    return (
        <TableView {...tableStyles} overflowMode={'wrap'} density={'compact'}>
            <TableHeader columns={columns}>
                {({ align, label, width }) => {
                    return (
                        <Column key={label} width={width} align={align}>
                            {label}
                        </Column>
                    );
                }}
            </TableHeader>
            <TableBody>
                {rowData.map((row) => {
                    return (
                        <Row key={`model-table-row-${row.id}`}>{columns.map((column) => column.component(row))}</Row>
                    );
                })}
            </TableBody>
        </TableView>
    );
};
