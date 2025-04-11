// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { LabelsRelationType } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { projectListRender as render } from '../../../../test-utils/projects-list-providers-render';
import { MORE_THAN_100_CHARS_NAME } from '../../../../test-utils/utils';
import {
    ProjectMetadata,
    ProjectType,
    STEPS,
} from '../../new-project-dialog-provider/new-project-dialog-provider.interface';
import { MAX_NUMBER_OF_CHARACTERS_OF_PROJECT_NAME, REQUIRED_PROJECT_NAME_VALIDATION_MESSAGE } from '../utils';
import { NameProject } from './name-project.component';

describe('Name project step', () => {
    const setValidationError = jest.fn();
    const mockMetadata: ProjectMetadata = {
        name: 'test',
        selectedDomains: [DOMAIN.SEGMENTATION],
        projectTypeMetadata: [
            { domain: DOMAIN.SEGMENTATION, labels: [], relation: LabelsRelationType.SINGLE_SELECTION },
        ],
        selectedTab: 'Detection',
        currentStep: STEPS.SELECT_TEMPLATE,
        projectType: ProjectType.SINGLE,
    };

    afterEach(() => {
        jest.clearAllMocks();
    });

    it("There's Name project step with name 'Project name' field", async () => {
        await render(
            <NameProject
                metadata={mockMetadata}
                updateProjectState={jest.fn()}
                setValidationError={setValidationError}
                goToNextStep={jest.fn()}
            />
        );

        const nameTextField = screen.getByRole('textbox');
        expect(nameTextField).toHaveValue('test');
    });

    it('Check if empty name will show error', async () => {
        await render(
            <NameProject
                metadata={mockMetadata}
                updateProjectState={jest.fn()}
                setValidationError={setValidationError}
                goToNextStep={jest.fn()}
            />
        );
        const nameTextField = screen.getByRole('textbox');

        fireEvent.change(nameTextField, { target: { value: 'test' } });
        fireEvent.change(nameTextField, { target: { value: '' } });

        expect(setValidationError).toHaveBeenCalled();
        expect(screen.getByText(REQUIRED_PROJECT_NAME_VALIDATION_MESSAGE)).toBeInTheDocument();
    });

    it('Check if name is limited to 100 characters', async () => {
        await render(
            <NameProject
                metadata={mockMetadata}
                updateProjectState={jest.fn()}
                setValidationError={setValidationError}
                goToNextStep={jest.fn()}
            />
        );
        const nameTextField = screen.getByRole('textbox');
        const stringWith100Chars = MORE_THAN_100_CHARS_NAME.substring(0, MAX_NUMBER_OF_CHARACTERS_OF_PROJECT_NAME);

        // Fill the input with the max number of chars
        fireEvent.change(nameTextField, { target: { value: '' } });
        fireEvent.change(nameTextField, { target: { value: stringWith100Chars } });

        // Try typing one more character
        await userEvent.type(nameTextField, 'a');

        expect(nameTextField).toHaveValue(stringWith100Chars);
    });

    it('Clear validation errors upon unmounting', async () => {
        const { unmount } = await render(
            <NameProject
                metadata={mockMetadata}
                updateProjectState={jest.fn()}
                setValidationError={setValidationError}
                goToNextStep={jest.fn()}
            />
        );

        expect(setValidationError).not.toHaveBeenCalled();

        // Force an error (Empty name)
        fireEvent.change(screen.getByRole('textbox'), { target: { value: '   ' } });
        expect(setValidationError).toHaveBeenCalled();

        unmount();

        await render(
            <NameProject
                metadata={mockMetadata}
                updateProjectState={jest.fn()}
                setValidationError={setValidationError}
                goToNextStep={jest.fn()}
            />
        );

        expect(screen.queryByText(REQUIRED_PROJECT_NAME_VALIDATION_MESSAGE)).not.toBeInTheDocument();
    });

    it('Should go to next step if the user presses "ENTER" key', async () => {
        const mockGoToNextStep = jest.fn();

        await render(
            <NameProject
                metadata={mockMetadata}
                updateProjectState={jest.fn()}
                setValidationError={setValidationError}
                goToNextStep={mockGoToNextStep}
            />
        );

        fireEvent.submit(screen.getByRole('textbox'));

        expect(mockGoToNextStep).toHaveBeenCalled();
    });
});
