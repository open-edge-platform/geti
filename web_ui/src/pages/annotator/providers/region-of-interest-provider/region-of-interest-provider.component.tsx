// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useContext, useMemo } from 'react';

import { getImageData } from '@shared/canvas-utils';
import { MissingProviderError } from '@shared/missing-provider-error';

import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { getBoundingBox, roiFromImage } from '../../../../core/annotations/math';
import { useSelectedMediaItem } from '../selected-media-item-provider/selected-media-item-provider.component';
import { useTaskChain } from '../task-chain-provider/task-chain-provider.component';

interface RegionOfInterestProviderProps {
    children: ReactNode;
}

interface RegionOfInterestContextProps {
    roi: RegionOfInterest;
    image: ImageData;
}

const RegionOfInterestContext = createContext<RegionOfInterestContextProps | undefined>(undefined);

const useContainerBoundingBox = (image: ImageData): RegionOfInterest => {
    const { inputs } = useTaskChain();
    const [inputAnnotation] = inputs.filter(({ isSelected }) => isSelected);

    return useMemo(() => {
        const container: RegionOfInterest = inputAnnotation?.shape
            ? getBoundingBox(inputAnnotation.shape)
            : roiFromImage(image);

        return container;
    }, [inputAnnotation, image]);
};

export const RegionOfInterestProvider = ({ children }: RegionOfInterestProviderProps): JSX.Element => {
    const { selectedMediaItem } = useSelectedMediaItem();

    const image = useMemo<ImageData>(
        () => (selectedMediaItem?.image !== undefined ? selectedMediaItem.image : getImageData(new Image())),
        [selectedMediaItem]
    );

    const roi = useContainerBoundingBox(image);

    const value = useMemo<RegionOfInterestContextProps>(
        () => ({
            roi,
            image,
        }),
        [roi, image]
    );

    return <RegionOfInterestContext.Provider value={value}>{children}</RegionOfInterestContext.Provider>;
};

export const useROI = (): RegionOfInterestContextProps => {
    const context = useContext(RegionOfInterestContext);

    if (context === undefined) {
        throw new MissingProviderError('useROI', 'RegionOfInterestProvider');
    }

    return context;
};
