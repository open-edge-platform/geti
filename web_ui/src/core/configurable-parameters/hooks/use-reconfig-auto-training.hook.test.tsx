// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import {
    ConfigurableParametersParams,
    ConfigurableParametersTaskChain,
} from '@shared/components/configurable-parameters/configurable-parameters.interface';
import { getReconfigureParametersDTO, updateSelectedParameter } from '@shared/components/configurable-parameters/utils';
import { renderHook, waitFor } from '@testing-library/react';

import { RequiredProviders } from '../../../test-utils/required-providers-render';
import QUERY_KEYS from '../../requests/query-keys';
import { createInMemoryApiModelConfigParametersService } from '../services/in-memory-api-model-config-parameters-service';
import { findAutoTrainingConfig } from '../utils';
import { useReconfigAutoTraining } from './use-reconfig-auto-training.hook';

jest.mock('@shared/components/configurable-parameters/utils', () => ({
    getReconfigureParametersDTO: jest.fn(() => ({})),
    updateSelectedParameter: jest.fn(() => ({})),
}));

const mockInvalidateQueries = jest.fn();
const mockCancelQueries = jest.fn();
const mockGetQueryData = jest.fn();
const mockSetQueryData = jest.fn();
const mockReconfigureParameters = jest.fn(() => Promise.resolve());

jest.mock('@tanstack/react-query', () => ({
    ...jest.requireActual('@tanstack/react-query'),
    useQueryClient: () => ({
        invalidateQueries: mockInvalidateQueries,
        cancelQueries: mockCancelQueries,
        getQueryData: mockGetQueryData,
        setQueryData: mockSetQueryData,
    }),
}));

const wrapper = ({ children }: { children: ReactNode }) => {
    const configParametersService = createInMemoryApiModelConfigParametersService();
    configParametersService.reconfigureParameters = mockReconfigureParameters;

    return <RequiredProviders configParametersService={configParametersService}>{children}</RequiredProviders>;
};

const getConfigParameters = (taskId: string, value: boolean) =>
    ({
        taskId,
        components: [
            {
                header: 'General',
                parameters: [
                    {
                        header: 'Auto-training',
                        value,
                    },
                ],
            },
        ],
    }) as unknown as ConfigurableParametersTaskChain;

describe('useReconfigAutoTraining', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    const mockedTrainingConfig = {
        id: '111::222::333',
        value: true,
    } as ConfigurableParametersParams;

    const projectIdentifier = { workspaceId: 'workspaceId', projectId: 'projectId', organizationId: 'organization-id' };
    const mockQueryKey = QUERY_KEYS.CONFIGURATION(projectIdentifier);

    const handleOptimisticUpdate = (taskId: string) => (config: ConfigurableParametersTaskChain[]) => {
        const autoTrainingConfig = findAutoTrainingConfig(taskId, config);
        autoTrainingConfig !== undefined && (autoTrainingConfig.value = !autoTrainingConfig.value);

        return config;
    };

    it('successful update', async () => {
        const taskId = 'taskId';
        const configParameters = [getConfigParameters(taskId, Boolean(mockedTrainingConfig.value))];

        const { result } = renderHook(() => useReconfigAutoTraining(projectIdentifier), {
            wrapper,
        });

        result.current.mutate({
            configParameters,
            newConfigParameter: mockedTrainingConfig,
            onOptimisticUpdate: handleOptimisticUpdate(taskId),
        });

        await waitFor(() => {
            expect(updateSelectedParameter).toHaveBeenCalledWith(
                configParameters,
                mockedTrainingConfig.id,
                expect.anything(),
                mockedTrainingConfig.value
            );
        });

        expect(getReconfigureParametersDTO).toHaveBeenCalled();
        expect(mockCancelQueries).toHaveBeenCalledWith({ queryKey: [mockQueryKey] });
        expect(mockSetQueryData).toHaveBeenCalledWith(mockQueryKey, [
            getConfigParameters(taskId, Boolean(mockedTrainingConfig.value)),
        ]);
        expect(mockGetQueryData).toHaveBeenCalledWith(mockQueryKey);
        expect(mockInvalidateQueries).not.toHaveBeenCalled();
    });

    it('request error', async () => {
        const taskId = 'taskId';
        const mockPreviousSnapshottedConfig: ConfigurableParametersTaskChain[] = [];
        jest.mocked(mockReconfigureParameters).mockRejectedValue({ message: 'test error' });
        jest.mocked(mockGetQueryData).mockReturnValue(mockPreviousSnapshottedConfig);

        const configParameters = [getConfigParameters(taskId, Boolean(mockedTrainingConfig.value))];

        const { result } = renderHook(() => useReconfigAutoTraining(projectIdentifier), {
            wrapper,
        });

        result.current.mutate({
            configParameters,
            newConfigParameter: mockedTrainingConfig,
            onOptimisticUpdate: handleOptimisticUpdate(taskId),
        });

        await waitFor(() => {
            expect(updateSelectedParameter).toHaveBeenCalledWith(
                configParameters,
                mockedTrainingConfig.id,
                expect.anything(),
                mockedTrainingConfig.value
            );
        });

        expect(mockGetQueryData).toHaveBeenCalledWith(mockQueryKey);
        expect(mockSetQueryData).toHaveBeenLastCalledWith(mockQueryKey, mockPreviousSnapshottedConfig);
        expect(mockInvalidateQueries).toHaveBeenCalled();
    });
});
