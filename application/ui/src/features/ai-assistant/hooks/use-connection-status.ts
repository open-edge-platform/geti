// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useCallback, useEffect, useState } from 'react';

import { getAiAgent } from '../agents';
import { useAiConnection } from '../connection';
import { claudeStatus } from '../transport/claude-transport';
import { codexStatus } from '../transport/codex-transport';
import { hasStoredKey } from '../transport/key-service';
import type { AssistantAccount } from '../types';

export interface ConnectionStatus {
    isLoading: boolean;
    isReady: boolean;
    account: AssistantAccount | null;
    error: string | null;
    refresh: () => void;
}

export const useConnectionStatus = (): ConnectionStatus => {
    const connection = useAiConnection();
    const [revision, setRevision] = useState(0);
    const [status, setStatus] = useState<Omit<ConnectionStatus, 'refresh'>>({
        isLoading: true,
        isReady: false,
        account: null,
        error: null,
    });
    const refresh = useCallback(() => setRevision((value) => value + 1), []);

    useEffect(() => {
        let active = true;
        const agent = getAiAgent(connection.agentId);
        setStatus({ isLoading: true, isReady: false, account: null, error: null });

        const check = async (): Promise<{ ready: boolean; account: AssistantAccount | null }> => {
            if (agent.method === 'api') {
                return { ready: await hasStoredKey(agent.credentialAccount ?? ''), account: null };
            }
            if (agent.id === 'openai-app') {
                const account = await codexStatus(true);
                return {
                    ready: account !== null,
                    account: account === null ? null : { type: 'chatgpt', ...account },
                };
            }
            const account = await claudeStatus();
            return { ready: account !== null, account };
        };

        void check()
            .then(({ ready, account }) => {
                if (active) setStatus({ isLoading: false, isReady: ready, account, error: null });
            })
            .catch((error: unknown) => {
                if (active) {
                    setStatus({
                        isLoading: false,
                        isReady: false,
                        account: null,
                        error:
                            error instanceof Error ? error.message : 'The assistant connection could not be checked.',
                    });
                }
            });

        return () => {
            active = false;
        };
    }, [connection.agentId, connection.executable, revision]);

    return { ...status, refresh };
};
