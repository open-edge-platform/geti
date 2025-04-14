// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

// This file is used to easily mock ResizeObserver so that we can test components
// that rely on useVirtual hooks

interface ResizeObserverListener {
    (rects: [{ contentRect: { width: number; height: number } }]): void;
}

export const resizeObserverListener: ResizeObserverListener | undefined = undefined;
