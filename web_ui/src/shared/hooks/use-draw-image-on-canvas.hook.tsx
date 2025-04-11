// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
