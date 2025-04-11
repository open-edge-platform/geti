// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { MEDIA_TYPE } from '../../core/media/base-media.interface';
import {
    AdvancedFilterOptions,
    SearchOptionsRule,
    SearchRuleField,
    SearchRuleOperator,
    SearchRuleShapeType,
} from '../../core/media/media-filter.interface';
import { KeyMap } from '../../shared/keyboard-events/keyboard.interface';
import { getMockedLabel } from '../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedImageMediaItem } from '../../test-utils/mocked-items-factory/mocked-media';
import {
    addOrUpdateFilterRule,
    concatByProperty,
    deleteEmptySpaceAndLastComa,
    filterPageMedias,
    findLabelsById,
    getLowercaseSplitNames,
    getRuleByField,
    getShapesFromText,
    getValidRules,
    hasLabelsDifference,
    isDate,
    isDigit,
    isEmptyRule,
    isKeyboardDelete,
    isUniqueRule,
    isValidInteger,
    lastCommaRegex,
    removeRuleById,
    textRegex,
} from './utils';

const getValidRule = (id = '123', field = SearchRuleField.MediaName): SearchOptionsRule => ({
    id,
    field,
    operator: SearchRuleOperator.Equal,
    value: 'test',
});

describe('media util', () => {
    it('textRegex', () => {
        expect(textRegex.test('abcd')).toBe(true);
        expect(textRegex.test('abcd123')).toBe(true);
        expect(textRegex.test('abc_abc')).toBe(true);
        expect(textRegex.test('abc-abc')).toBe(true);
        expect(textRegex.test('123abcd')).toBe(true);
        expect(textRegex.test('12332')).toBe(true);
        expect(textRegex.test('12332-123')).toBe(true);
    });

    it('hasLabelsDifference', () => {
        expect(hasLabelsDifference([getMockedLabel({ id: 'label-1' })], [getMockedLabel({ id: 'label-1' })])).toBe(
            false
        );
        expect(hasLabelsDifference([getMockedLabel({ id: 'label-1' })], [getMockedLabel({ id: 'label-2' })])).toBe(
            true
        );
    });

    it('lastCommaRegex', () => {
        expect(lastCommaRegex.test('abc,')).toBe(true);
        expect(lastCommaRegex.test('abc ,')).toBe(true);
        expect(lastCommaRegex.test('abc , ')).toBe(true);
        expect(lastCommaRegex.test(', abc')).toBe(false);
        expect(lastCommaRegex.test('abc,abc')).toBe(false);
    });

    it('isValidInteger', () => {
        expect(isValidInteger(Number.MAX_SAFE_INTEGER + 1)).toBe(false);
        expect(isValidInteger(Number.NaN)).toBe(false);
        expect(isValidInteger(Number.MAX_SAFE_INTEGER)).toBe(true);
    });

    describe('isDigit', () => {
        const numbersAndLetters = Array.from({ length: 43 }).map((_, i) => i + 48);

        test.each([numbersAndLetters])('keyCode from 48 to 90', (keyCode) => {
            expect(isDigit(keyCode)).toBe(true);
        });
    });

    it('isEmptyRule', () => {
        expect(isEmptyRule({ id: '123', value: 'test', field: '', operator: SearchRuleOperator.Equal })).toBe(true);
        expect(isEmptyRule({ id: '123', value: 'test', field: SearchRuleField.LabelId, operator: '' })).toBe(true);
        expect(
            isEmptyRule({ id: '123', value: '', field: SearchRuleField.LabelId, operator: SearchRuleOperator.Equal })
        ).toBe(true);
    });

    it('findLabelsById', () => {
        const labels = [
            getMockedLabel({ name: 'label-1', id: 'label-1' }),
            getMockedLabel({ name: 'label-2', id: 'label-2' }),
            getMockedLabel({ name: 'label-3', id: 'label-3' }),
        ];

        expect(findLabelsById(['123'], labels)).toEqual([]);
        expect(findLabelsById([labels[0].id, labels[2].id], labels)).toEqual([labels[0], labels[2]]);
    });

    it('isUniqueRule', () => {
        const rules: SearchOptionsRule[] = [
            { id: '123', field: SearchRuleField.MediaHeight, operator: SearchRuleOperator.In, value: '' },
            { id: '321', field: SearchRuleField.LabelId, operator: SearchRuleOperator.Equal, value: ['123', '322'] },
        ];

        const newRule: SearchOptionsRule = {
            id: '213',
            field: SearchRuleField.LabelId,
            operator: SearchRuleOperator.Equal,
            value: ['123'],
        };

        expect(isUniqueRule(newRule, rules)).toBe(true);
        expect(isUniqueRule(rules[0], rules)).toBe(false);
    });

    describe('getRuleByField', () => {
        it('has match', () => {
            const ruleOne = getValidRule('123', SearchRuleField.MediaName);
            const ruleTwo = getValidRule('321', SearchRuleField.LabelId);
            expect(getRuleByField([ruleOne, ruleTwo], SearchRuleField.LabelId)).toEqual([ruleTwo]);
        });

        it('does not has match', () => {
            const ruleOne = getValidRule('123', SearchRuleField.MediaName);
            const ruleTwo = getValidRule('321', SearchRuleField.LabelId);
            expect(getRuleByField([ruleOne, ruleTwo], SearchRuleField.AnnotationCreationDate)).toEqual([]);
        });

        it('empty rules', () => {
            expect(getRuleByField([], SearchRuleField.AnnotationCreationDate)).toEqual([]);
        });

        it('falsy parameters', () => {
            expect(getRuleByField(undefined, SearchRuleField.AnnotationCreationDate)).toEqual([]);
        });
    });

    describe('addOrUpdateFilterRule', () => {
        const newRule = {
            field: SearchRuleField.MediaName,
            operator: SearchRuleOperator.Equal,
            value: 'test',
            id: 'test-rule',
        };

        it('empty options', () => {
            expect(addOrUpdateFilterRule({}, { ...newRule })).toEqual({
                condition: 'and',
                rules: [newRule],
            });
        });

        it('add new rule when field and operator are different', () => {
            const oldRule = {
                id: '1',
                field: SearchRuleField.MediaHeight,
                operator: SearchRuleOperator.Greater,
                value: 0,
            };
            expect(
                addOrUpdateFilterRule(
                    {
                        condition: 'and',
                        rules: [oldRule],
                    },
                    { ...newRule }
                )
            ).toEqual({
                condition: 'and',
                rules: [oldRule, newRule],
            });
        });

        it('replace rule when there is already rule with the same id', () => {
            const oldRule = {
                id: 'test-rule',
                field: SearchRuleField.MediaName,
                operator: SearchRuleOperator.Equal,
                value: 0,
            };
            expect(
                addOrUpdateFilterRule(
                    {
                        condition: 'and',
                        rules: [oldRule],
                    },
                    { ...newRule }
                )
            ).toEqual({
                condition: 'and',
                rules: [newRule],
            });
        });
    });

    describe('getValidRules', () => {
        const emptyRule: SearchOptionsRule = { id: '', field: '', operator: '', value: '' };

        it('has empty rules', () => {
            expect(getValidRules([emptyRule, getValidRule(), emptyRule])).toEqual([getValidRule()]);
        });

        it('all valid  but not unique', () => {
            expect(getValidRules([getValidRule(), getValidRule()])).toEqual([getValidRule()]);
        });

        it('all valid and unique', () => {
            expect(getValidRules([getValidRule(), getValidRule('321')])).toEqual([getValidRule(), getValidRule('321')]);
        });

        it('invalid rules', () => {
            expect(getValidRules([emptyRule, emptyRule])).toEqual([]);
        });

        it('empty rules', () => {
            expect(getValidRules([])).toEqual([]);
        });

        it('falsy parameters', () => {
            expect(getValidRules()).toEqual([]);
        });
    });

    describe('removeRuleById', () => {
        const mockOptions: AdvancedFilterOptions = { condition: 'and', rules: [getValidRule('321')] };

        it('empty options', () => {
            expect(removeRuleById({}, '123')).toEqual({});
        });

        it('should return an empty obj when last rule is removed', () => {
            expect(removeRuleById(mockOptions, '321')).toEqual({});
        });

        it('filterId does not mach current rules', () => {
            expect(removeRuleById(mockOptions, '123')).toEqual(mockOptions);
        });

        it('match rule is removed', () => {
            expect(
                removeRuleById({ ...mockOptions, rules: [...mockOptions.rules, getValidRule('123')] }, '123')
            ).toEqual(mockOptions);
        });
    });

    it('deleteEmptySpaceAndLastComa', () => {
        expect(deleteEmptySpaceAndLastComa(',123')).toBe(',123');
        expect(deleteEmptySpaceAndLastComa(',123,')).toBe(',123');
        expect(deleteEmptySpaceAndLastComa(' 123, 321,')).toBe('123,321');
    });

    it('getLowercaseSplitNames', () => {
        expect(getLowercaseSplitNames('test, Test2, TEST3,')).toEqual(['test', 'test2', 'test3']);
        expect(getLowercaseSplitNames('test, Test2, TEST3')).toEqual(['test', 'test2', 'test3']);
        expect(getLowercaseSplitNames('test, Test2 TEST3')).toEqual(['test', 'test2test3']);
        expect(getLowercaseSplitNames('')).toEqual([]);
    });

    it('isKeyboardDelete', () => {
        expect(isKeyboardDelete({ code: KeyMap.Enter } as never)).toBe(false);
        expect(isKeyboardDelete({ code: KeyMap.Delete } as never)).toBe(true);
        expect(isKeyboardDelete({ code: KeyMap.Backspace } as never)).toBe(true);
    });

    describe('concatByProperty', () => {
        it('full object', () => {
            const objTest = [
                {
                    name: 'testName',
                    age: 'testAge',
                },
                {
                    name: 'testName2',
                    age: 'testAge',
                },
            ];
            expect(concatByProperty(objTest, 'name')).toBe('testName, testName2, ');
        });

        it('empty object', () => {
            const objTest: { name: string }[] = [];
            expect(concatByProperty(objTest, 'name')).toBe('');
        });
    });

    describe('getShapesFromText', () => {
        it('single value', () => {
            expect(getShapesFromText(SearchRuleShapeType.ELLIPSE)).toEqual([{ key: 'ELLIPSE', text: 'Circle' }]);
        });

        it('multiple values', () => {
            expect(getShapesFromText([SearchRuleShapeType.ELLIPSE, SearchRuleShapeType.POLYGON])).toEqual([
                { key: 'ELLIPSE', text: 'Circle' },
                { key: 'POLYGON', text: 'Polygon' },
            ]);
        });
    });

    it('isDate', () => {
        expect(isDate(SearchRuleField.MediaUploadDate)).toBe(true);
        expect(isDate(SearchRuleField.AnnotationCreationDate)).toBe(true);
    });

    describe('filterPageMedias', () => {
        const mockedMedia = getMockedImageMediaItem({ identifier: { type: MEDIA_TYPE.IMAGE, imageId: '1111' } });
        const mockedMediaTwo = getMockedImageMediaItem({ identifier: { type: MEDIA_TYPE.IMAGE, imageId: '2222' } });

        const mockedResponse = {
            pages: [
                {
                    media: [mockedMedia, mockedMediaTwo],
                    totalImages: 1,
                    totalMatchedImages: 1,
                    totalVideos: 0,
                    totalMatchedVideoFrames: 0,
                    totalMatchedVideos: 0,
                    nextPage: undefined,
                },
            ],
            pageParams: [null],
        };

        it('removes items with matched identifier', () => {
            expect(filterPageMedias(mockedResponse, [{ imageId: '1111', type: MEDIA_TYPE.IMAGE }])).toEqual(
                expect.objectContaining({ pages: [expect.objectContaining({ media: [mockedMediaTwo] })] })
            );
        });

        it('keep elements with different identifier', () => {
            expect(filterPageMedias(mockedResponse, [{ type: MEDIA_TYPE.IMAGE, imageId: '111' }])).toEqual(
                expect.objectContaining({ pages: [expect.objectContaining({ media: [mockedMedia, mockedMediaTwo] })] })
            );
        });
    });
});
