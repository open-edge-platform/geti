// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
