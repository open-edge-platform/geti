// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { getMockedDatasetIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { useCameraParams } from '../../hooks/camera-params.hook';
import { getUseCameraParams } from '../../test-utils/camera-params';
import { TakeShotsButton } from './take-shots-button.component';

const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockedNavigate,
}));

jest.mock('../../hooks/camera-params.hook', () => ({
    ...jest.requireActual('../../hooks/camera-params.hook'),
    useCameraParams: jest.fn(),
}));

const mockedDatasetIdentifier = getMockedDatasetIdentifier();

describe('TakeShotsButton', () => {
    const renderApp = async ({
        defaultLabelId = '',
        hasDefaultLabel = false,
    }: {
        defaultLabelId?: string;
        hasDefaultLabel?: boolean;
    }) => {
        jest.mocked(useCameraParams).mockReturnValue(
            getUseCameraParams({ defaultLabelId, hasDefaultLabel, ...mockedDatasetIdentifier })
        );

        render(<TakeShotsButton />);
    };

    it('redirects with defaultLabelId param', async () => {
        const defaultLabelId = '123321';
        await renderApp({ hasDefaultLabel: true, defaultLabelId });

        await waitFor(() => {
            fireEvent.click(screen.getByRole('button'));
        });

        expect(mockedNavigate).toHaveBeenCalledWith(expect.stringContaining(`?defaultLabelId=${defaultLabelId}`));
    });

    it('call navigation handler', async () => {
        await renderApp({});

        await waitFor(() => {
            fireEvent.click(screen.getByRole('button'));
        });
        expect(mockedNavigate).toHaveBeenCalledWith(
            '/organizations/organization-id/workspaces/workspace-id/projects/project-id/datasets/dataset-id/camera'
        );
    });
});
