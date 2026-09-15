// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useCallback, useEffect, useState } from 'react';

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

/**
 * Resolves whether the selected provider is usable: an API key present in the
 * credential store, or a signed-in ChatGPT account.
 */
export const useConnectionStatus = (): ConnectionStatus => {
    const { provider } = useAiConnection();

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

        const resolve = async () => {
            if (provider === 'api') {
                const stored = await hasStoredKey();

                if (isCurrent) {
                    setHasKey(stored);
                }

                return;
            }

            const signedIn = await codexStatus();

            if (isCurrent) {
                setAccount(signedIn);
            }
        };

        void resolve()
            .catch((reason: unknown) => {
                if (isCurrent) {
                    setError(reason instanceof Error ? reason.message : 'Could not check the connection.');
                }
            })
            .finally(() => {
                if (isCurrent) {
                    setIsLoading(false);
                }
            });

        return () => {
            isCurrent = false;
        };
    }, [provider, revision]);

    return {
        isLoading,
        isReady: provider === 'api' ? hasKey : account !== null,
        hasKey,
        account,
        error,
        refresh,
    };
};
