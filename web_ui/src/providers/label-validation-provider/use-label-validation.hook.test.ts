// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { act, renderHook } from '@testing-library/react';

import { LabelItemType } from '../../core/labels/label-tree-view.interface';
import { DOMAIN } from '../../core/projects/core.interface';
import { getMockedTreeLabel } from '../../test-utils/mocked-items-factory/mocked-labels';
import { useLabelValidation } from './use-label-validation.hook';

const baseLabel = getMockedTreeLabel({ name: 'Cat' });

describe('useLabelValidation', () => {
    it('validates label name (valid case)', () => {
        const { result } = renderHook(() =>
            useLabelValidation({
                projectLabels: [baseLabel],
                labelType: LabelItemType.LABEL,
            })
        );

        act(() => {
            const valid = result.current.validateName('Dog');
            expect(valid).toBe(true);
        });

        expect(result.current.validationErrors.name).toBe('');
    });

    it('validates label name (duplicate)', () => {
        const { result } = renderHook(() =>
            useLabelValidation({
                projectLabels: [baseLabel],
                labelType: LabelItemType.LABEL,
            })
        );

        act(() => {
            const valid = result.current.validateName('Cat');
            expect(valid).toBe(false);
        });

        expect(result.current.validationErrors.name).toMatch(/already exists/i);
    });

    it('validates hotkey (valid case)', () => {
        const { result } = renderHook(() =>
            useLabelValidation({
                projectLabels: [baseLabel],
                usedAnnotatorHotkeys: ['b'],
            })
        );

        act(() => {
            const valid = result.current.validateHotkey('c');
            expect(valid).toBe(true);
        });

        expect(result.current.validationErrors.hotkey).toBe('');
    });

    it('validates hotkey (duplicate)', () => {
        const { result } = renderHook(() =>
            useLabelValidation({
                projectLabels: [baseLabel],
                usedAnnotatorHotkeys: ['a'],
            })
        );

        act(() => {
            const valid = result.current.validateHotkey('a');
            expect(valid).toBe(false);
        });

        expect(result.current.validationErrors.hotkey).toMatch(
            /This hotkey is reserved for operations on annotator page/i
        );
    });

    it('validates tree (valid)', () => {
        const { result } = renderHook(() =>
            useLabelValidation({
                domain: DOMAIN.DETECTION,
                labels: [baseLabel],
            })
        );

        act(() => {
            const valid = result.current.validateTree();
            expect(valid).toBe(true);
        });

        expect(result.current.treeValidationError).toBeUndefined();
    });

    it('validates tree (invalid - empty)', () => {
        const { result } = renderHook(() =>
            useLabelValidation({
                domain: DOMAIN.DETECTION,
                labels: [],
            })
        );

        act(() => {
            const valid = result.current.validateTree();
            expect(valid).toBe(false);
        });

        expect(result.current.treeValidationError).toMatch(/at least/i);
    });

    it('calls setDialogValidationError when error state changes', () => {
        const setDialogValidationError = jest.fn();
        const { result } = renderHook(() =>
            useLabelValidation({
                projectLabels: [baseLabel],
                setDialogValidationError,
            })
        );

        act(() => {
            result.current.validateName('Cat'); // duplicate
        });

        act(() => {
            result.current.updateDialogValidationError();
        });

        expect(setDialogValidationError).toHaveBeenCalledWith(expect.stringMatching(/fix all the errors/i));
    });

    it('hasError is true if any error exists', () => {
        const { result } = renderHook(() =>
            useLabelValidation({
                projectLabels: [baseLabel],
            })
        );

        act(() => {
            result.current.validateName('Cat'); // duplicate
        });

        expect(result.current.hasError).toBe(true);
    });

    it('hasError is false if no errors', () => {
        const { result } = renderHook(() =>
            useLabelValidation({
                projectLabels: [baseLabel],
            })
        );

        act(() => {
            result.current.validateName('Dog');
        });

        expect(result.current.hasError).toBe(false);
    });
});
