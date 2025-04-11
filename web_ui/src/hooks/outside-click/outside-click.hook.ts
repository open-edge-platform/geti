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

import { MutableRefObject, RefObject, useCallback } from 'react';

import { DOMRefValue } from '@react-types/shared';

import { useEventListener } from '../event-listener/event-listener.hook';

interface OutsideClickProps {
    ref: MutableRefObject<HTMLElement | null>;
    callback: (e: PointerEvent) => void;
    element?: RefObject<Element>;
}

export const useOutsideClick = ({ ref, callback, element }: OutsideClickProps): void => {
    const outsideClickHandler = useCallback(
        (event: PointerEvent) => {
            if (!ref.current) return;

            try {
                if (!ref.current.contains(event.target as Node)) callback(event);
            } catch (_) {
                if (
                    !(ref.current as unknown as DOMRefValue<HTMLDivElement>)
                        .UNSAFE_getDOMNode()
                        ?.contains(event.target as Node)
                ) {
                    callback(event);
                }
            }
        },
        [ref, callback]
    );

    useEventListener('pointerdown', outsideClickHandler, element);
};
