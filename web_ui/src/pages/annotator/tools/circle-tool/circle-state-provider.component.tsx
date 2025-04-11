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

import { createContext, Dispatch, ReactNode, SetStateAction, useContext, useMemo, useState } from 'react';

import { MissingProviderError } from '../../../../shared/missing-provider-error';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { getMaxCircleRadius } from './utils';

interface CircleStateContextProps {
    isBrushSizePreviewVisible: boolean;
    setIsBrushSizePreviewVisible: Dispatch<SetStateAction<boolean>>;

    circleRadiusSize: number;
    setCircleRadiusSize: Dispatch<SetStateAction<number>>;

    maxCircleRadius: number;
}

const CircleStateContext = createContext<CircleStateContextProps | undefined>(undefined);

interface CircleStateProviderProps {
    children: ReactNode;
}

export const CircleStateProvider = ({ children }: CircleStateProviderProps): JSX.Element => {
    const { getToolSettings } = useAnnotationToolContext();
    const circleSettings = getToolSettings(ToolType.CircleTool);

    const [circleRadiusSize, setCircleRadiusSize] = useState<number>(circleSettings.size);
    const [isBrushSizePreviewVisible, setIsBrushSizePreviewVisible] = useState<boolean>(false);
    const { roi } = useROI();
    const maxCircleRadius = useMemo(() => getMaxCircleRadius(roi), [roi]);

    return (
        <CircleStateContext.Provider
            value={{
                isBrushSizePreviewVisible,
                setIsBrushSizePreviewVisible,
                circleRadiusSize,
                setCircleRadiusSize,
                maxCircleRadius,
            }}
        >
            {children}
        </CircleStateContext.Provider>
    );
};

export const useCircleState = (): CircleStateContextProps => {
    const context = useContext(CircleStateContext);

    if (context === undefined) {
        throw new MissingProviderError('useCircleState', 'CircleStateProvider');
    }

    return context;
};
