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

import { useCallback, useRef } from 'react';

export const useSingleStackFn = <
    Callback extends (...args: Parameters<Callback>) => Promise<Awaited<ReturnType<Callback>>>,
>(
    fn: Callback
) => {
    const resolveRef = useRef<() => void>();
    const rejectRef = useRef<() => void>();
    const isProcessing = useRef(false);

    const wrappedFn = useCallback(
        async (...args: Parameters<Callback>): Promise<Awaited<ReturnType<Callback>>> => {
            // Wait for the previous function call to be finished
            await new Promise<void>(async (resolve, reject) => {
                // Continue on if we are not waiting for the result of a previous invokation
                if (!isProcessing.current) {
                    return resolve();
                }

                // If the function was invoked while waiting for the previous result then
                // we reject the previous invocation
                if (rejectRef.current) {
                    rejectRef.current();
                    rejectRef.current = undefined;
                    resolveRef.current = undefined;
                }

                // Let the previous invocation resolve this call, or let any subsequent calls
                // cancel this call
                rejectRef.current = reject;
                resolveRef.current = resolve;
            });

            try {
                isProcessing.current = true;
                const result = await fn(...args);
                return result;
            } catch (error) {
                // Reject subsequent invocations as something unexpected made the current invocation fail
                if (rejectRef.current) {
                    rejectRef.current();
                    rejectRef.current = undefined;
                    resolveRef.current = undefined;
                }
                throw error;
            } finally {
                isProcessing.current = false;

                // Resolve any subsequent invocations that were waiting for this function to complete
                if (resolveRef.current) {
                    resolveRef.current();
                    rejectRef.current = undefined;
                    resolveRef.current = undefined;
                }
            }
        },
        [fn]
    );

    return wrappedFn;
};
