// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
