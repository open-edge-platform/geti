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

import { createContext, ReactNode, useContext, useState } from 'react';

import union from 'lodash/union';

import { MissingProviderError } from '../../../../shared/missing-provider-error';

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
