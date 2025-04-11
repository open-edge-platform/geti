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

import { getMockedSupportedAlgorithm } from '../../../../../core/supported-algorithms/services/test-utils';
import { ModelTemplatesNames } from '../../../../../core/supported-algorithms/supported-algorithms.interface';
import { getModelTemplateDetails, getModelTemplatesAlgorithms } from './utils';

describe('Utils for training model dialog', () => {
    describe('getAccuracySpeedBalanceAlgorithms', () => {
        it('should return undefined when there are no algorithms', () => {
            expect(getModelTemplatesAlgorithms([])).toBe(undefined);
        });

        it('should return only accuracy template if there is only one algorithm', () => {
            const accuracyAlgorithm = getMockedSupportedAlgorithm({ isDefaultAlgorithm: true });

            expect(getModelTemplatesAlgorithms([accuracyAlgorithm])).toEqual({
                accuracyAlgorithm: {
                    ...accuracyAlgorithm,
                    templateName: ModelTemplatesNames.ACCURACY,
                },
            });
        });

        it('should return accuracy and speed templates if there are only two algorithms, accuracy gets the algorithm that is default, speed gets the left one', () => {
            const accuracyAlgorithm = getMockedSupportedAlgorithm({
                name: 'Algorithm 1',
                gigaflops: 2.4,
                isDefaultAlgorithm: true,
            });
            const speedAlgorithm = getMockedSupportedAlgorithm({ name: 'Algorithm 2', gigaflops: 1.3 });
            const mockedSupportedAlgorithm = [accuracyAlgorithm, speedAlgorithm];

            expect(getModelTemplatesAlgorithms(mockedSupportedAlgorithm)).toEqual({
                accuracyAlgorithm: {
                    ...accuracyAlgorithm,
                    templateName: ModelTemplatesNames.ACCURACY,
                },
                speedAlgorithm: {
                    ...speedAlgorithm,
                    templateName: ModelTemplatesNames.SPEED,
                },
            });
        });

        it('should return balance, accuracy, speed templates if there are at least three algorithms, accuracy gets algorithms that has the highest gigaflops value, speed has the lowest gigaflops value, balance got the middle algorithm', () => {
            const accuracyAlgorithm = getMockedSupportedAlgorithm({
                name: 'Algorithm 1',
                gigaflops: 2.4,
                isDefaultAlgorithm: true,
            });
            const speedAlgorithm = getMockedSupportedAlgorithm({ name: 'Algorithm 4', gigaflops: 0.9 });
            const balanceAlgorithm = getMockedSupportedAlgorithm({ name: 'Algorithm 2', gigaflops: 1.3 });

            const mockedSupportedAlgorithm = [
                accuracyAlgorithm,
                balanceAlgorithm,
                speedAlgorithm,
                getMockedSupportedAlgorithm({ name: 'Algorithm 3', gigaflops: 1.1 }),
            ];

            expect(getModelTemplatesAlgorithms(mockedSupportedAlgorithm)).toEqual({
                accuracyAlgorithm: {
                    ...accuracyAlgorithm,
                    templateName: ModelTemplatesNames.ACCURACY,
                },
                speedAlgorithm: {
                    ...speedAlgorithm,
                    templateName: ModelTemplatesNames.SPEED,
                },
                balanceAlgorithm: {
                    ...balanceAlgorithm,
                    templateName: ModelTemplatesNames.BALANCE,
                },
            });
        });

        it('should return balance, accuracy, speed templates if there are at least three algorithms and none of "preselected" templates is a default, accuracy gets algorithms that has the highest gigaflops value, speed has the lowest gigaflops value, balance got the middle algorithm', () => {
            const accuracyAlgorithm = getMockedSupportedAlgorithm({
                name: 'Algorithm 1',
                gigaflops: 2.4,
            });
            const speedAlgorithm = getMockedSupportedAlgorithm({ name: 'Algorithm 4', gigaflops: 0.9 });
            const preSelectedBalanceAlgorithm = getMockedSupportedAlgorithm({
                name: 'Algorithm 2',
                gigaflops: 1.3,
            });
            const balanceAlgorithm = getMockedSupportedAlgorithm({
                name: 'Algorithm 3',
                gigaflops: 1.1,
                isDefaultAlgorithm: true,
            });

            const mockedSupportedAlgorithm = [
                accuracyAlgorithm,
                preSelectedBalanceAlgorithm,
                speedAlgorithm,
                balanceAlgorithm,
            ];

            expect(getModelTemplatesAlgorithms(mockedSupportedAlgorithm)).toEqual({
                accuracyAlgorithm: {
                    ...accuracyAlgorithm,
                    templateName: ModelTemplatesNames.ACCURACY,
                },
                speedAlgorithm: {
                    ...speedAlgorithm,
                    templateName: ModelTemplatesNames.SPEED,
                },
                balanceAlgorithm: {
                    ...balanceAlgorithm,
                    templateName: ModelTemplatesNames.BALANCE,
                },
            });
        });
    });

    describe('getModelTemplateDetails', () => {
        const modelTemplateId = 'model-template-id';

        it('should return object with empty strings if there are no algorithms', () => {
            expect(getModelTemplateDetails(modelTemplateId, [])).toEqual({
                templateName: '',
                summary: '',
            });
        });

        it('should return object with template name and summary of the algorithm', () => {
            const algorithmDescription = 'Test description';
            const templateName = ModelTemplatesNames.ACCURACY;
            expect(
                getModelTemplateDetails(modelTemplateId, [
                    getMockedSupportedAlgorithm({ modelTemplateId, templateName, summary: algorithmDescription }),
                ])
            ).toEqual({
                templateName,
                summary: algorithmDescription,
            });
        });
    });
});
