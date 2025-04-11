// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { createContext, useContext, useEffect, useState } from 'react';

import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { usePrevious } from '../../../../hooks/use-previous/use-previous.hook';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import { MissingProviderError } from '../../../../shared/missing-provider-error';
import { useInteractiveSegmentation } from '../../hooks/use-interactive-segmentation.hook';
import { StateProviderProps } from '../tools.interface';
import UndoRedoProvider from '../undo-redo/undo-redo-provider.component';
import useUndoRedoState from '../undo-redo/use-undo-redo-state';
import { RITMPoint, RITMResult } from './ritm-tool.interface';

export interface RITMStateContextProps {
    loadImage: (imageData: ImageData) => void;
    isLoading: boolean;
    isProcessing: boolean;
    reset: () => void;
    cancel: () => void;
    execute: (area: RegionOfInterest, givenPoints: RITMPoint[], outputShape: ShapeType) => void;
    setBox: (box: RegionOfInterest | null) => void;
    box: RegionOfInterest | null;
    result: RITMResult | null;
}

const RITMStateContext = createContext<RITMStateContextProps | undefined>(undefined);

export const RITMStateProvider = ({ children }: StateProviderProps): JSX.Element => {
    const { addNotification } = useNotification();

    const [box, setBox] = useState<RegionOfInterest | null>(null);
    const [result, setResult, undoRedoActions] = useUndoRedoState<RITMResult | null>(null);

    const previousResult = usePrevious(result);

    const showNotificationError = () => {
        addNotification({
            message: 'Interactive segmentation failed, please reload and try again',
            type: NOTIFICATION_TYPE.ERROR,
        });
        reset();
    };

    const {
        cleanMask,
        isLoading,
        reset: resetWorker,
        loadImage,
        mutation,
        cancel,
    } = useInteractiveSegmentation({
        showNotificationError,
        onSuccess: setResult,
    });

    useEffect(() => {
        if (result && previousResult && result.points.length < previousResult.points.length) {
            cleanMask();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [result]);

    const execute = (area: RegionOfInterest, givenPoints: RITMPoint[], outputShape: ShapeType) => {
        mutation.mutateAsync({ area, givenPoints, outputShape });
    };

    const reset = async () => {
        setBox(null);
        setResult(null);
        resetWorker();
        undoRedoActions.reset();
    };

    return (
        <RITMStateContext.Provider
            value={{
                loadImage,
                isLoading,
                isProcessing: mutation.isPending,
                result,
                execute,
                reset,
                box,
                setBox,
                cancel,
            }}
        >
            <UndoRedoProvider state={undoRedoActions}>{children}</UndoRedoProvider>
        </RITMStateContext.Provider>
    );
};

export const useRITMState = (): RITMStateContextProps => {
    const context = useContext(RITMStateContext);

    if (context === undefined) {
        throw new MissingProviderError('useRITMState', 'RITMStateProvider');
    }

    return context;
};
