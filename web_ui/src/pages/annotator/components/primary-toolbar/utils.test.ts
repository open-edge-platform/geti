// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { renderHook } from '@testing-library/react';

import { labelFromUser } from '../../../../core/annotations/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedTask, mockedTaskContextProps } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { SelectingTool } from '../../tools/selecting-tool/index';
import { shouldDisableTools, useDisabledTools, useDrawingTools } from './utils';

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(),
}));

describe('Primary toolbar utils', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    test.each(Object.keys(DOMAIN))(
        'useDrawingTools returns all supported tools for %o but the Select tool',
        async (domain) => {
            const { result } = renderHook(() => useDrawingTools([domain as DOMAIN]));
            const tools = result.current;

            expect(tools.includes(SelectingTool)).toBeFalsy();
        }
    );

    it('shouldDisableTools returns false if it is a single task project', () => {
        const fakeContext = fakeAnnotationToolContext({});
        const tasks = [getMockedTask({ id: 'mock-task' })];

        expect(shouldDisableTools(fakeContext, tasks, tasks[0])).toEqual(false);
    });

    it('shouldDisableTools returns false there is no previousTask', () => {
        const fakeContext = fakeAnnotationToolContext({});
        const tasks = [getMockedTask({ id: 'mock-task-1' }), getMockedTask({ id: 'mock-task-2' })];
        expect(shouldDisableTools(fakeContext, tasks, null)).toEqual(false);
    });

    it('shouldDisableTools returns false if previousTask has annotations', () => {
        const mockLabel = getMockedLabel({ id: 'some-label' });
        const mockTaskOne = getMockedTask({ id: 'mock-task-1', labels: [mockLabel] });
        const mockTaskTwo = getMockedTask({ id: 'mock-task-2' });
        const fakeContext = fakeAnnotationToolContext({
            annotations: [getMockedAnnotation({ labels: [labelFromUser(mockLabel)] })],
        });
        const tasks = [mockTaskOne, mockTaskTwo];

        expect(shouldDisableTools(fakeContext, tasks, mockTaskTwo)).toEqual(false);
    });

    it('shouldDisableTools returns true if previousTask has no annotations', () => {
        const mockTaskOne = getMockedTask({ id: 'mock-task-1' });
        const mockTaskTwo = getMockedTask({ id: 'mock-task-2' });
        const fakeContext = fakeAnnotationToolContext({
            annotations: [],
        });

        const tasks = [mockTaskOne, mockTaskTwo];

        expect(shouldDisableTools(fakeContext, tasks, mockTaskTwo)).toEqual(true);
    });

    it('useDisabledTools should not toggle SelectTool if shouldDisableTools returns false', () => {
        const mockLabel = getMockedLabel({ id: 'some-label' });
        const mockTaskOne = getMockedTask({ id: 'mock-task-1', labels: [mockLabel] });
        const mockTaskTwo = getMockedTask({ id: 'mock-task-2' });
        const mockToggleTool = jest.fn();
        const fakeContext = fakeAnnotationToolContext({
            tasks: [mockTaskOne, mockTaskTwo],
            selectedTask: mockTaskTwo,
            toggleTool: mockToggleTool,
            annotations: [getMockedAnnotation({ labels: [{ ...mockLabel, source: { userId: '123321' } }] })],
        });

        jest.mocked(useTask).mockReturnValueOnce(
            mockedTaskContextProps({ tasks: [mockTaskOne, mockTaskTwo], selectedTask: mockTaskTwo })
        );

        renderHook(() => useDisabledTools(fakeContext));

        expect(mockToggleTool).not.toHaveBeenCalled();
    });

    it('useDisabledTools should toggle SelectTool if shouldDisableTools returns true', () => {
        const mockToggleTool = jest.fn();
        const mockTaskOne = getMockedTask({ id: 'mock-task-1' });
        const mockTaskTwo = getMockedTask({ id: 'mock-task-2' });
        const fakeContext = fakeAnnotationToolContext({
            toggleTool: mockToggleTool,
            annotations: [],
        });

        jest.mocked(useTask).mockReturnValueOnce(
            mockedTaskContextProps({ tasks: [mockTaskOne, mockTaskTwo], selectedTask: mockTaskTwo })
        );

        renderHook(() => useDisabledTools(fakeContext));

        expect(mockToggleTool).toHaveBeenCalledWith(ToolType.SelectTool);
    });
});
