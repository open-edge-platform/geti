// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, Dispatch, ReactNode, SetStateAction, useContext, useMemo, useState } from 'react';

import { MissingProviderError } from '@shared/missing-provider-error';

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
