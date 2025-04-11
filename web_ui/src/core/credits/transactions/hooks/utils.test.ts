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

import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import {
    getMockedTransaction,
    getMockedTransactionsAggregate,
} from '../../../../test-utils/mocked-items-factory/mocked-transactions';
import { TransactionsAggregatesKey } from '../transactions.interface';
import { setTransactionAggregatesProjectName, setTransactionProjectName } from './utils';

describe('Transactions hook utils', () => {
    describe('setTransactionProjectName', () => {
        it('project-id does not match', () => {
            const mockedProject = getMockedProject({});
            const mockedTransaction = getMockedTransaction();
            expect(setTransactionProjectName([mockedProject], [mockedTransaction])).toEqual([
                { ...mockedTransaction, projectName: `Undefined project - id: ${mockedTransaction.projectId}` },
            ]);
        });

        it('match project-id', () => {
            const mockedProject = getMockedProject({});
            const mockedTransaction = getMockedTransaction({ projectId: mockedProject.id });
            expect(setTransactionProjectName([mockedProject], [mockedTransaction])).toEqual([
                { ...mockedTransaction, projectName: mockedProject.name },
            ]);
        });
    });

    describe('setTransactionAggregatesProjectName', () => {
        it('project-id does not match', () => {
            const mockedProject = getMockedProject({});
            const mockedTransactionsAggregate = getMockedTransactionsAggregate();
            expect(setTransactionAggregatesProjectName([mockedProject], [mockedTransactionsAggregate])).toEqual([
                { ...mockedTransactionsAggregate, projectName: `Undefined project - id: project_id_784` },
            ]);
        });

        it('match project-id', () => {
            const mockedProject = getMockedProject({});
            const mockedTransactionsAggregate = getMockedTransactionsAggregate({
                group: [{ key: TransactionsAggregatesKey.PROJECT, value: mockedProject.id }],
            });
            expect(setTransactionAggregatesProjectName([mockedProject], [mockedTransactionsAggregate])).toEqual([
                { ...mockedTransactionsAggregate, projectName: mockedProject.name },
            ]);
        });
    });
});
