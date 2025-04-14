// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
