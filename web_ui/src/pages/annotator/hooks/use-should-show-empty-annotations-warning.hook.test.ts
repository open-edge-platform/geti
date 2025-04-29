// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { renderHook } from '@testing-library/react';

import { getMockedAnnotation } from '../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedImageMediaItem } from '../../../test-utils/mocked-items-factory/mocked-media';
import {
    SelectedMediaItemProps,
    useSelectedMediaItem,
} from '../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useTaskChain } from '../providers/task-chain-provider/task-chain-provider.component';
import { TaskChainContextProps } from '../providers/task-chain-provider/task-chain.interface';
import { TaskContextProps, useTask } from '../providers/task-provider/task-provider.component';
import { useShouldShowEmptyAnnotationsWarning } from './use-should-show-empty-annotations-warning.hook';

jest.mock('../providers/selected-media-item-provider/selected-media-item-provider.component', () => ({
    ...jest.requireActual('../providers/selected-media-item-provider/selected-media-item-provider.component'),
    useSelectedMediaItem: jest.fn(),
}));

jest.mock('../providers/task-chain-provider/task-chain-provider.component', () => ({
    ...jest.requireActual('../providers/task-chain-provider/task-chain-provider.component'),
    useTaskChain: jest.fn(() => ({ inputs: [] })),
}));

jest.mock('../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => ({ isTaskChainSecondTask: false })),
}));

const input = { ...getMockedAnnotation({}), outputs: [] };

describe('useShouldShowEmptyAnnotationsWarning', () => {
    it('falsy media item', () => {
        jest.mocked(useSelectedMediaItem).mockReturnValue({ selectedMediaItem: undefined } as SelectedMediaItemProps);
        jest.mocked(useTaskChain).mockReturnValue({ inputs: [input] } as unknown as TaskChainContextProps);
        jest.mocked(useTask).mockReturnValue({ isTaskChainSecondTask: true } as unknown as TaskContextProps);

        const { result } = renderHook(() => useShouldShowEmptyAnnotationsWarning());
        expect(result.current).toBe(false);
    });

    it('empty inputs and other task', () => {
        const selectedMediaItem = getMockedImageMediaItem({});
        jest.mocked(useSelectedMediaItem).mockReturnValue({ selectedMediaItem } as SelectedMediaItemProps);
        jest.mocked(useTaskChain).mockReturnValue({ inputs: [] } as unknown as TaskChainContextProps);
        jest.mocked(useTask).mockReturnValue({ isTaskChainSecondTask: false } as unknown as TaskContextProps);

        const { result } = renderHook(() => useShouldShowEmptyAnnotationsWarning());
        expect(result.current).toBe(false);
    });

    it('has input and other task', () => {
        const selectedMediaItem = getMockedImageMediaItem({});
        jest.mocked(useSelectedMediaItem).mockReturnValue({ selectedMediaItem } as SelectedMediaItemProps);
        jest.mocked(useTaskChain).mockReturnValue({ inputs: [input] } as unknown as TaskChainContextProps);
        jest.mocked(useTask).mockReturnValue({ isTaskChainSecondTask: false } as unknown as TaskContextProps);

        const { result } = renderHook(() => useShouldShowEmptyAnnotationsWarning());
        expect(result.current).toBe(false);
    });

    it('empty input and second task', () => {
        const selectedMediaItem = getMockedImageMediaItem({});
        jest.mocked(useSelectedMediaItem).mockReturnValue({ selectedMediaItem } as SelectedMediaItemProps);
        jest.mocked(useTaskChain).mockReturnValue({ inputs: [] } as unknown as TaskChainContextProps);
        jest.mocked(useTask).mockReturnValue({ isTaskChainSecondTask: true } as unknown as TaskContextProps);

        const { result } = renderHook(() => useShouldShowEmptyAnnotationsWarning());
        expect(result.current).toBe(true);
    });
});
