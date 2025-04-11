// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { mockedConfigParamData } from '../../../../../core/configurable-parameters/services/test-utils';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { ReconfigureModels } from './reconfigure-models.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        projectId: 'project-id',
        organizationId: 'organization-id',
        workspaceId: 'workspace_1',
    }),
}));

describe('Reconfigure parameters of the model', () => {
    const foldUnfoldButtonId = 'fold-unfold-button';
    const firstTaskFoldUnfoldButtonId = `${idMatchingFormat(mockedConfigParamData[0].taskTitle)}-${foldUnfoldButtonId}`;
    const secondTaskFoldUnfoldButtonId = `${idMatchingFormat(
        mockedConfigParamData[1].taskTitle
    )}-${foldUnfoldButtonId}`;

    const renderReconfigureModels = async (): Promise<void> => {
        render(<ReconfigureModels />);

        fireEvent.click(screen.getByRole('button', { name: 'Reconfigure active model' }));
    };

    it('should the reconfiguration of the parameters dialog appear', async () => {
        await renderReconfigureModels();

        expect(screen.getByText('Reconfigure parameters for active model')).toBeInTheDocument();
    });

    it('should reconfigure button in the dialog be disabled', async () => {
        await renderReconfigureModels();

        expect(screen.getByRole('button', { name: 'Reconfigure' })).toBeDisabled();
    });

    it('should the first task`s component tab be selected and unfolded by default', async () => {
        await renderReconfigureModels();

        const firstTab = await screen.findByText(mockedConfigParamData[0].components[0].header);

        expect(screen.getByText(mockedConfigParamData[0].taskTitle)).toBeInTheDocument();
        expect(firstTab.parentNode).toHaveClass('tabItemSelected', { exact: false });

        mockedConfigParamData[0].components[0].parameters?.forEach((parameter) => {
            expect(screen.getByText(parameter.header)).toBeInTheDocument();
        });
    });

    it('should the first task be folded and the second one unfolded', async () => {
        await renderReconfigureModels();

        fireEvent.click(await screen.findByTestId(firstTaskFoldUnfoldButtonId));
        fireEvent.click(screen.getByTestId(secondTaskFoldUnfoldButtonId));

        mockedConfigParamData[1].components.forEach((component) => {
            expect(screen.getByText(component.header)).toBeInTheDocument();
        });
    });

    it('should the content change based on the selected component of given task', async () => {
        await renderReconfigureModels();

        fireEvent.click(await screen.findByTestId(secondTaskFoldUnfoldButtonId));
        mockedConfigParamData[1].components[0].groups?.forEach((group) => {
            expect(screen.queryByText(group.header)).not.toBeInTheDocument();
        });

        const firstComponent = screen.getByText(mockedConfigParamData[1].components[0].header);
        const secondComponent = screen.getByText(mockedConfigParamData[1].components[1].header);
        fireEvent.click(firstComponent);

        expect(firstComponent.parentNode).toHaveClass('tabItemSelected', { exact: false });
        expect(secondComponent.parentNode).not.toHaveClass('tabItemSelected', { exact: false });

        mockedConfigParamData[1].components[0].groups?.forEach((group) => {
            expect(screen.getByText(group.header)).toBeInTheDocument();
        });

        fireEvent.click(secondComponent);
        expect(secondComponent.parentNode).toHaveClass('tabItemSelected', { exact: false });
        expect(firstComponent.parentNode).not.toHaveClass('tabItemSelected', { exact: false });

        await waitFor(() => {
            mockedConfigParamData[1].components[1].groups?.forEach((group) => {
                expect(screen.getByText(group.header)).toBeInTheDocument();
            });
        });
    });
});
