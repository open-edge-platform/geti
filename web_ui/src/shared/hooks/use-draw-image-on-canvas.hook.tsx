// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

interface DrawImageOnCanvasProps {
    image: ImageData | undefined;
    enabled?: boolean;
}

export const useDrawImageOnCanvas = (props: DrawImageOnCanvasProps) => {
    const { image, enabled = true } = props;
    const ref = useRef<HTMLCanvasElement>(null);

    // Normal image
    useEffect(() => {
        if (!ref.current || image === undefined) {
            return;
        }

        const ctx = ref.current.getContext('2d');

        if (ctx === null || ctx === undefined) {
            return;
        }

        ctx.putImageData(image, 0, 0);
    }, [image, enabled]);

    return ref;
};
