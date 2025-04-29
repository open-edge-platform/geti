// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
