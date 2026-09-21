// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useCallback, useEffect, useRef, useState } from 'react';

import { useAiConnection } from '../connection';
import { codexStatus } from '../transport/codex-transport';
import { hasStoredKey } from '../transport/key-service';
import type { CodexAccount } from '../types';

export interface ConnectionStatus {
    isLoading: boolean;
    /** Whether the selected provider can answer a question right now. */
    isReady: boolean;
    hasKey: boolean;
    account: CodexAccount | null;
    error: string | null;
    refresh: () => void;
}

const describe = (reason: unknown): string =>
    reason instanceof Error ? reason.message : 'Could not check the connection.';

/**
 * Resolves whether the selected provider is usable: an API key present in the
 * credential store, or a signed-in ChatGPT account. Both providers are probed
 * so the settings can show, at a glance, which one is already connected.
 */
export const useConnectionStatus = (): ConnectionStatus => {
    const { provider, executable } = useAiConnection();
    const previousExecutable = useRef(executable);

    const [isLoading, setIsLoading] = useState(true);
    const [hasKey, setHasKey] = useState(false);
    const [account, setAccount] = useState<CodexAccount | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [revision, setRevision] = useState(0);

    const refresh = useCallback(() => setRevision((previous) => previous + 1), []);

    useEffect(() => {
        let isCurrent = true;

        setIsLoading(true);
        setError(null);
        if (previousExecutable.current !== executable) {
            previousExecutable.current = executable;
            setAccount(null);
        }

        void Promise.allSettled([hasStoredKey(), codexStatus(revision > 0)]).then(([key, codex]) => {
            if (!isCurrent) {
                return;
            }

            if (key.status === 'fulfilled') setHasKey(key.value);
            // A failed probe says nothing about whether the user signed out.
            // Only a successful account/read returning null may clear an account.
            if (codex.status === 'fulfilled') setAccount(codex.value);

            // Only the provider in use may raise an error; a failed probe of the
            // other one simply reads as "not connected".
            const selected = provider === 'api' ? key : codex;

            setError(selected.status === 'rejected' ? describe(selected.reason) : null);
            setIsLoading(false);
        });

        return () => {
            isCurrent = false;
        };
    }, [provider, executable, revision]);

    return {
        isLoading,
        isReady: provider === 'api' ? hasKey : account !== null,
        hasKey,
        account,
        error,
        refresh,
    };
};
