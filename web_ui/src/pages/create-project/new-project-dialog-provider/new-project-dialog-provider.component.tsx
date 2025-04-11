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

import { createContext, ReactNode, useContext } from 'react';

import { MissingProviderError } from '../../../shared/missing-provider-error';
import { NewProjectDialogContextProps } from './new-project-dialog-provider.interface';
import { useProjectDialogSteps } from './use-project-dialog-steps.hook';

interface NewProjectDialogProviderProps {
    children: ReactNode;
}

const NewProjectDialogContext = createContext<NewProjectDialogContextProps | undefined>(undefined);

export const NewProjectDialogProvider = ({ children }: NewProjectDialogProviderProps): JSX.Element => {
    const {
        component,
        hasNextStep,
        hasPreviousStep,
        validationError,
        projectCreationState,
        resetSteps,
        goToNextStep,
        goToPreviousStep,
        updateProjectState,
    } = useProjectDialogSteps();

    return (
        <NewProjectDialogContext.Provider
            value={{
                resetSteps,
                goToNextStep,
                goToPreviousStep,
                updateProjectState,
                hasNextStep,
                hasPreviousStep,
                validationError,
                content: component,
                metadata: projectCreationState,
            }}
        >
            {children}
        </NewProjectDialogContext.Provider>
    );
};

export const useNewProjectDialog = (): NewProjectDialogContextProps => {
    const context = useContext(NewProjectDialogContext);

    if (context === undefined) {
        throw new MissingProviderError('useNewProjectDialog', 'NewProjectDialogProvider');
    }

    return context;
};
