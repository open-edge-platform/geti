// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useContext, useState } from 'react';

import union from 'lodash/union';

import { MissingProviderError } from '../../shared/missing-provider-error';

interface SelectedProviderProps {
    isSelected: (id: string) => boolean;
    addSelected: (id: string[]) => void;
    removeSelected: (id: string) => void;
    setSelected: (id: string[]) => void;
}

const SelectedContext = createContext<SelectedProviderProps | undefined>(undefined);

export const SelectedProvider = ({ children, selectedIds = [] }: { children: ReactNode; selectedIds?: string[] }) => {
    const [selected, setSelected] = useState(selectedIds);

    const addSelected = (values: string[]) => {
        setSelected((prevValues) => {
            return union(prevValues, values);
        });
    };

    const removeSelected = (value: string) => {
        setSelected((prevValues) => {
            return prevValues.filter((currentValue) => currentValue !== value);
        });
    };

    const isSelected = (value: string) => {
        return selected.includes(value);
    };

    return (
        <SelectedContext.Provider value={{ isSelected, addSelected, removeSelected, setSelected }}>
            {children}
        </SelectedContext.Provider>
    );
};

export const useSelected = () => {
    const context = useContext(SelectedContext);

    if (context === undefined) {
        throw new MissingProviderError('useSelected', 'SelectedProvider');
    }

    return context;
};
