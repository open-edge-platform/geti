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

import { FormEvent, useMemo, useState } from 'react';

import { Form } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import isFunction from 'lodash/isFunction';

import { LimitedTextField } from '../../../../shared/components/limited-text-field/limited-text-field.component';
import { ProjectMetadata } from '../../new-project-dialog-provider/new-project-dialog-provider.interface';
import { MAX_NUMBER_OF_CHARACTERS_OF_PROJECT_NAME, REQUIRED_PROJECT_NAME_VALIDATION_MESSAGE } from '../utils';

interface NameProjectProps {
    setValidationError: (message?: string) => void;
    metadata: ProjectMetadata;
    updateProjectState: (projectState: Partial<ProjectMetadata>) => void;
    goToNextStep: (() => void | null) | undefined;
}

export const NameProject = ({
    setValidationError,
    metadata,
    updateProjectState,
    goToNextStep,
}: NameProjectProps): JSX.Element => {
    const { name } = metadata;

    const [projectName, setProjectName] = useState<string>(name);

    const hasError = useMemo(() => isEmpty(projectName.trim()), [projectName]);

    const validateProjectName = (inputProjectName: string): void => {
        if (isEmpty(inputProjectName)) {
            setValidationError(REQUIRED_PROJECT_NAME_VALIDATION_MESSAGE);
        } else {
            updateProjectState({ name: inputProjectName });
            setValidationError(undefined);
        }
    };

    const handleProjectNameChange = (inputProjectName: string): void => {
        setProjectName(inputProjectName);
        validateProjectName(inputProjectName.trim());
    };

    const handleSubmit = (event: FormEvent) => {
        event.preventDefault();

        !hasError && isFunction(goToNextStep) && goToNextStep();
    };

    return (
        <Form marginBottom={'size-300'} onSubmit={handleSubmit}>
            <LimitedTextField
                id='project-name-input-id'
                width='100%'
                marginBottom={'size-50'}
                label='Project name'
                value={projectName}
                // eslint-disable-next-line jsx-a11y/no-autofocus
                autoFocus
                validationState={hasError ? 'invalid' : undefined}
                errorMessage={hasError ? REQUIRED_PROJECT_NAME_VALIDATION_MESSAGE : undefined}
                maxLength={MAX_NUMBER_OF_CHARACTERS_OF_PROJECT_NAME}
                onFocus={(event) => (event.target as HTMLInputElement).select()}
                onChange={handleProjectNameChange}
            />
        </Form>
    );
};
