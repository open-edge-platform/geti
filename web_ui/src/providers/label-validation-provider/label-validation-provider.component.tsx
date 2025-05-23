// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useContext } from 'react';

import { MissingProviderError } from '../../shared/missing-provider-error';
import { UseLabelValidationProps, UseLabelValidationResult } from './label-validation-types';
import { useLabelValidation } from './use-label-validation.hook';

const LabelValidationContext = createContext<UseLabelValidationResult | null>(null);

export const LabelValidationProvider = ({ children, ...props }: UseLabelValidationProps & { children: ReactNode }) => {
    const validation = useLabelValidation(props);

    return <LabelValidationContext.Provider value={validation}>{children}</LabelValidationContext.Provider>;
};

export const useLabelValidationContext = (): UseLabelValidationResult => {
    const context = useContext(LabelValidationContext);

    if (!context) {
        throw new MissingProviderError('useLabelValidationContext', 'LabelValidationProvider');
    }

    return context;
};
