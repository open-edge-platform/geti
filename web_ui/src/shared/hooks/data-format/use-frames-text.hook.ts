// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export const useFramesText = (frames: number | undefined): string => {
    return !!frames ? `${frames} frame${frames === 1 ? '' : 's'}` : '';
};
