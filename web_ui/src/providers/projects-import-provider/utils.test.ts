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

import { getParsedLocalStorage, setParsedLocalStorage } from '../../shared/utils';
import { getMockedWorkspaceIdentifier } from '../../test-utils/mocked-items-factory/mocked-identifiers';
import { ProjectImportItem, ProjectImportStatusValues } from './project-import.interface';
import {
    getImportProjectId,
    getProjectImportItem,
    getProjectImportItems,
    getProjectImportItemsKey,
    getProjectStatusBaseData,
    isProjectImportingStatus,
    setProjectImportItems,
} from './utils';

jest.mock('../../shared/utils', () => ({
    ...jest.requireActual('../../shared/utils'),
    setParsedLocalStorage: jest.fn(),
    getParsedLocalStorage: jest.fn(),
}));

const workspaceIdentifier = getMockedWorkspaceIdentifier();

describe('project-import-provider utils', () => {
    it('setProjectImportItems', () => {
        const testData = {};
        setProjectImportItems(workspaceIdentifier, testData);

        expect(setParsedLocalStorage).toHaveBeenCalledWith(getProjectImportItemsKey(workspaceIdentifier), testData);
    });

    it('getProjectImportItems', () => {
        getProjectImportItems(workspaceIdentifier);

        expect(getParsedLocalStorage).toHaveBeenCalledWith(getProjectImportItemsKey(workspaceIdentifier));
    });

    it('getImportProjectId', () => {
        expect(getImportProjectId('')).toBe('');
        expect(getImportProjectId(null)).toBe('');
        expect(getImportProjectId('resumable/test')).toBe('test');
    });

    it('getProjectStatusBaseData', () => {
        const data = { fileId: '123', fileSize: 10, fileName: 'fiel test' } as ProjectImportItem;
        expect(getProjectStatusBaseData(data)).toEqual(data);
    });

    it('isProjectImportingStatus', () => {
        expect(
            isProjectImportingStatus({
                status: ProjectImportStatusValues.IMPORTING_INTERRUPTED,
            } as ProjectImportItem)
        ).toBe(true);

        expect(
            isProjectImportingStatus({
                status: ProjectImportStatusValues.IMPORTING,
            } as ProjectImportItem)
        ).toBe(true);
    });

    describe('getProjectImportItem', () => {
        it('valid LS', () => {
            const fileId = '123';
            const response = 'test-response';
            jest.mocked(getParsedLocalStorage).mockReturnValue({ [fileId]: response });

            expect(getProjectImportItem(workspaceIdentifier, '')).toBe(null);
            expect(getProjectImportItem(workspaceIdentifier, '321')).toBe(null);
            expect(getProjectImportItem(workspaceIdentifier, fileId)).toBe(response);
        });

        it('empty LS', () => {
            global.localStorage.removeItem(getProjectImportItemsKey(workspaceIdentifier));
            jest.mocked(getParsedLocalStorage).mockReturnValue(null);

            expect(getProjectImportItem(workspaceIdentifier, '')).toBe(null);
            expect(getProjectImportItem(workspaceIdentifier, '321')).toBe(null);
        });
    });
});
