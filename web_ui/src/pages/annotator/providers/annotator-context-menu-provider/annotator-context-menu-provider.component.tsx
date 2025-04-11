// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { createContext, ReactNode, useContext, useReducer, useState } from 'react';

import isEqual from 'lodash/isEqual';
import noop from 'lodash/noop';

import { ContextMenu, ContextMenuProps } from '../../../../shared/components/context-menu/context-menu.component';
import { MissingProviderError } from '../../../../shared/missing-provider-error';
import { useZoom } from '../../zoom/zoom-provider.component';
import { getContextMenuPosition } from './utils';

interface AnnotatorContextConfig
    extends Omit<ContextMenuProps, 'isVisible' | 'handleClose' | 'getContextMenuPosition'> {
    contextId: string | null;
}

interface AnnotatorContextMenuProviderProps {
    children: ReactNode;
}

interface AnnotatorContextMenuContextProps {
    showContextMenu: (inputContextConfig: AnnotatorContextConfig) => void;
    hideContextMenu: () => void;
    contextConfig: AnnotatorContextConfig;
}

const AnnotatorContextMenuContext = createContext<AnnotatorContextMenuContextProps | undefined>(undefined);

const INITIAL_CONTEXT_CONFIG: AnnotatorContextConfig = {
    contextId: null,
    menuPosition: { top: 0, left: 0 },
    menuItems: [],
    ariaLabel: '',
    handleMenuAction: noop,
};

const reducer = (
    state: AnnotatorContextConfig,
    nextState: Partial<AnnotatorContextConfig>
): AnnotatorContextConfig => ({
    ...state,
    ...nextState,
});

export const AnnotatorContextMenuProvider = ({ children }: AnnotatorContextMenuProviderProps): JSX.Element => {
    const [isVisible, setIsVisible] = useState<boolean>(false);
    const [contextConfig, dispatch] = useReducer(reducer, INITIAL_CONTEXT_CONFIG);
    const { setIsZoomDisabled } = useZoom();

    const handleClose = () => {
        setIsVisible(false);
    };

    const showContextMenu = (inputContextConfig: AnnotatorContextConfig): void => {
        // In case user already has a context menu and decided to do right-click in another place
        // we want to smoothly hide current menu and show in another place with right animation
        if (isVisible) {
            setIsVisible(false);

            setTimeout(() => {
                setIsVisible(true);

                dispatch(inputContextConfig);
            }, 150);
            return;
        }

        setIsVisible(true);
        setIsZoomDisabled(true);

        dispatch(inputContextConfig);
    };

    const hideContextMenu = () => {
        if (isVisible) {
            handleClose();
            !isEqual(INITIAL_CONTEXT_CONFIG, contextConfig) && dispatch(INITIAL_CONTEXT_CONFIG);
            setIsZoomDisabled(false);
        }
    };

    return (
        <AnnotatorContextMenuContext.Provider value={{ showContextMenu, hideContextMenu, contextConfig }}>
            {children}
            <ContextMenu
                isVisible={isVisible}
                handleMenuAction={contextConfig.handleMenuAction}
                ariaLabel={contextConfig.ariaLabel}
                menuItems={contextConfig.menuItems}
                menuPosition={contextConfig.menuPosition}
                disabledKeys={contextConfig.disabledKeys}
                handleClose={hideContextMenu}
                getContextMenuPosition={getContextMenuPosition}
            />
        </AnnotatorContextMenuContext.Provider>
    );
};

export const useAnnotatorContextMenu = (): AnnotatorContextMenuContextProps => {
    const context = useContext(AnnotatorContextMenuContext);

    if (context === undefined) {
        throw new MissingProviderError('useAnnotatorContextMenu', 'AnnotatorContextMenuProvider');
    }

    return context;
};
