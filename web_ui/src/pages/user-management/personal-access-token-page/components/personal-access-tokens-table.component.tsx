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

import { FC, useState } from 'react';

import { Cell, Column, Flex, Row, TableBody, TableHeader, TableView, useCollator, View } from '@adobe/react-spectrum';
import { SortDescriptor } from '@react-types/shared';
import get from 'lodash/get';
import isEmpty from 'lodash/isEmpty';

import { PartialPersonalAccessToken } from '../../../../core/personal-access-tokens/personal-access-tokens.interface';
import { CasualCell } from '../../../../shared/components/table/components/casual-cell/casual-cell.component';
import { TableCellProps } from '../../../../shared/components/table/table.interface';
import { Tag } from '../../../../shared/components/tag/tag.component';
import { SpectrumTableLoadingState } from '../../../../shared/utils';
import { PersonalAccessTokenMenu } from './personal-access-tokens-menu.component';
import { sortPersonalAccessTokens } from './utils';

export const enum PERSONAL_ACCESS_TOKENS_TABLE_COLUMNS {
    CREATION_DATE = 'createdAt',
    NAME = 'name',
    DESCRIPTION = 'description',
    CODE = 'partial',
    EXPIRATION_DATE = 'expiresAt',
    MORE_ACTIONS = 'moreActions',
}

interface PersonalAccessTokensTableProps {
    tokens: PartialPersonalAccessToken[] | undefined;
    isLoading: boolean;
}

const isExpiredToken = (tokenExpirationDate: string): boolean => {
    const today = new Date().toISOString();

    return tokenExpirationDate.localeCompare(today) < 0;
};

const ExpiredTokenBadge = () => {
    return <Tag text={'Expired'} style={{ backgroundColor: 'var(--brand-coral-coral-shade1)' }} withDot={false} />;
};

export const PersonalAccessTokensTable: FC<PersonalAccessTokensTableProps> = ({
    tokens,
    isLoading,
}: PersonalAccessTokensTableProps) => {
    const [sortDescriptor, setSortDescriptor] = useState<SortDescriptor>();
    const collator = useCollator({});
    const tokenItems = sortPersonalAccessTokens(tokens, sortDescriptor, collator);

    if (isEmpty(tokens)) {
        return null;
    }

    const columns = [
        {
            label: 'Creation date',
            dataKey: PERSONAL_ACCESS_TOKENS_TABLE_COLUMNS.CREATION_DATE,
            component: (data: TableCellProps) => <CasualCell {...data} />,
            isSortable: true,
        },
        {
            label: 'Name',
            dataKey: PERSONAL_ACCESS_TOKENS_TABLE_COLUMNS.NAME,
            component: (data: TableCellProps) => <CasualCell {...data} />,
            isSortable: false,
        },
        {
            label: 'Description',
            dataKey: PERSONAL_ACCESS_TOKENS_TABLE_COLUMNS.DESCRIPTION,
            component: (data: TableCellProps) => <CasualCell {...data} />,
            isSortable: true,
        },
        {
            label: 'Code',
            dataKey: PERSONAL_ACCESS_TOKENS_TABLE_COLUMNS.CODE,
            component: (data: TableCellProps) => <CasualCell {...data} />,
        },
        {
            label: 'Expiration Date',
            dataKey: PERSONAL_ACCESS_TOKENS_TABLE_COLUMNS.EXPIRATION_DATE,
            component: (data: TableCellProps) => {
                const expiredToken = isExpiredToken(data.rowData.expiresAt);

                if (expiredToken) {
                    return (
                        <Flex gap={'size-100'} alignItems={'center'}>
                            <CasualCell {...data} />
                            <ExpiredTokenBadge />
                        </Flex>
                    );
                }

                return <CasualCell {...data} />;
            },
            isSortable: true,
        },
        {
            label: '',
            dataKey: PERSONAL_ACCESS_TOKENS_TABLE_COLUMNS.MORE_ACTIONS,
            component: (data: TableCellProps) => <PersonalAccessTokenMenu token={data.rowData} {...data} />,
        },
    ];

    return (
        <View>
            <TableView
                id='personal-access-tokens-table-id'
                aria-label='Personal Access Tokens table'
                selectionMode='none'
                sortDescriptor={sortDescriptor}
                onSortChange={setSortDescriptor}
            >
                <TableHeader columns={columns}>
                    {({ label, dataKey: key }) => (
                        <Column
                            key={key}
                            hideHeader={key === PERSONAL_ACCESS_TOKENS_TABLE_COLUMNS.MORE_ACTIONS}
                            allowsSorting={key !== PERSONAL_ACCESS_TOKENS_TABLE_COLUMNS.MORE_ACTIONS}
                        >
                            {label}
                        </Column>
                    )}
                </TableHeader>
                <TableBody items={tokenItems} loadingState={isLoading ? SpectrumTableLoadingState.loading : undefined}>
                    {(token) => {
                        return (
                            <Row key={token.id}>
                                {(columnKey) => {
                                    const column = columns.find(({ dataKey }) => dataKey === columnKey);

                                    if (column === undefined) {
                                        return <Cell>N/A</Cell>;
                                    }

                                    const expiredToken = isExpiredToken(token.expiresAt);
                                    const expiredStyles = {
                                        textDecorationLine: 'line-through',
                                    };

                                    const cellProps: TableCellProps = {
                                        cellData: get(token, `${columnKey}`, 'N/A'),
                                        rowData: token,
                                        dataKey: `${columnKey}`,
                                        isScrolling: false,
                                        columnIndex: 1,
                                        rowIndex: 1,
                                    };

                                    return (
                                        <Cell>
                                            {
                                                <column.component
                                                    {...cellProps}
                                                    styles={expiredToken ? expiredStyles : undefined}
                                                />
                                            }
                                        </Cell>
                                    );
                                }}
                            </Row>
                        );
                    }}
                </TableBody>
            </TableView>
        </View>
    );
};
