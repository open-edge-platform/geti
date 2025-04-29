// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { waitFor } from '@testing-library/react';

import { renderHookWithProviders } from '../../../test-utils/render-hook-with-providers';
import { ProjectProvider } from '../providers/project-provider/project-provider.component';
import { useTotalCreditPrice } from './use-credits-to-consume.hook';

const mockedGetAllTaskDatasetStatistics = jest.fn();
jest.mock('../../../core/statistics/hooks/use-dataset-statistics.hook', () => ({
    useDatasetStatistics: () => ({
        useGetAllTaskDatasetStatistics: mockedGetAllTaskDatasetStatistics,
    }),
}));

const wrapper = ({ children }: { children: ReactNode }) => {
    return (
        <ProjectProvider
            projectIdentifier={{
                workspaceId: 'workspace-id',
                projectId: 'project-id',
                organizationId: 'organization-id',
            }}
        >
            {children}
        </ProjectProvider>
    );
};

const renderTotalCreditPrice = () => {
    return renderHookWithProviders(useTotalCreditPrice, { wrapper });
};

describe('useTotalCreditPrice', () => {
    it('loading ', async () => {
        mockedGetAllTaskDatasetStatistics.mockReturnValue({ isLoading: true });
        const { result } = renderTotalCreditPrice();

        await waitFor(() => {
            expect(result.current.isLoading).toBe(true);
        });
        expect(result.current.getCreditPrice()).toEqual({ totalCreditsToConsume: null, totalMedias: null });
    });

    it('single task', async () => {
        mockedGetAllTaskDatasetStatistics.mockReturnValue({
            data: { tasks: [{ annotatedFrames: 2, annotatedImages: 5 }] },
            isLoading: false,
        });
        const { result } = renderTotalCreditPrice();

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });
        expect(result.current.getCreditPrice()).toEqual({ totalCreditsToConsume: 7, totalMedias: 7 });
    });

    describe('task chain', () => {
        const tasks = [
            {
                id: '123',
                annotatedFrames: 0,
                annotatedImages: 7,
                objectsPerLabel: [
                    { id: '6613ab0c00989c5aa51a117a', value: 10 },
                    { id: '6613ab0c00989c5aa51a117d', value: 10 },
                ],
            },
            {
                id: '321',
                annotatedFrames: 0,
                annotatedImages: 1,
                objectsPerLabel: [
                    { id: '6613ab0c00989c5aa51a117a', value: 2 },
                    { id: '6613ab0c00989c5aa51a117d', value: 2 },
                ],
            },
        ];

        it('first task', async () => {
            const [{ id: firstTaskId }] = tasks;
            mockedGetAllTaskDatasetStatistics.mockReturnValue({ data: { tasks }, isLoading: false });
            const { result } = renderTotalCreditPrice();

            await waitFor(() => {
                expect(result.current.getCreditPrice(firstTaskId)).toEqual({
                    totalCreditsToConsume: 7,
                    totalMedias: 7,
                });
            });
        });

        it('second task', async () => {
            const [, { id: secondTaskId }] = tasks;
            mockedGetAllTaskDatasetStatistics.mockReturnValue({ data: { tasks }, isLoading: false });
            const { result } = renderTotalCreditPrice();

            await waitFor(() => {
                expect(result.current.getCreditPrice(secondTaskId)).toEqual({
                    totalCreditsToConsume: 20,
                    totalMedias: 20,
                });
            });
        });

        it('all task', async () => {
            mockedGetAllTaskDatasetStatistics.mockReturnValue({ data: { tasks }, isLoading: false });
            const { result } = renderTotalCreditPrice();

            await waitFor(() => {
                expect(result.current.isLoading).toBe(false);
            });
            expect(result.current.getCreditPrice()).toEqual({ totalCreditsToConsume: 27, totalMedias: 27 });
        });
    });
});
