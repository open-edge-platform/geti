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

import { RefObject, useEffect, useLayoutEffect, useRef } from 'react';

function determineTargetElement<ElementType extends Element = Element>(
    element?: RefObject<ElementType> | ElementType | null
): ElementType | (Window & typeof globalThis) | null {
    if (element === undefined) {
        return window;
    }

    if (element === null) {
        return null;
    }

    if ('current' in element) {
        return element.current;
    }

    return element;
}

type EventType = GlobalEventHandlersEventMap & WindowEventHandlersEventMap & DocumentEventMap;

export function useEventListener<
    EventName extends keyof EventType,
    Handler extends (event: EventType[EventName]) => void,
    ElementType extends Element = Element,
>(eventName: EventName, handler: Handler, element?: RefObject<ElementType> | ElementType | null): void {
    const savedHandler = useRef<Handler>(handler);

    useLayoutEffect(() => {
        savedHandler.current = handler;
    }, [handler]);

    useEffect(() => {
        const targetElement = determineTargetElement(element);

        if (targetElement === null) {
            return;
        }

        const eventListener: (event: EventType[EventName]) => void = (event) => {
            if (savedHandler.current !== undefined) {
                savedHandler.current(event);
            }
        };

        targetElement.addEventListener(eventName, eventListener as EventListenerOrEventListenerObject);

        return () => {
            targetElement.removeEventListener(eventName, eventListener as EventListenerOrEventListenerObject);
        };
    }, [eventName, element]);
}
