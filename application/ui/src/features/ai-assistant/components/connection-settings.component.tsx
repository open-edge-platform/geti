// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from 'react';

import { Button, ComboBox, Content, Flex, InlineAlert, Item, Section, Text, TextField } from '@geti-ui/ui';

import { availableAgentsForVendor, getAiAgent } from '../agents';
import { groupModelIds, type AiModelGroup } from '../config';
import { setAiAgent, setAiConnection, useAiConnection } from '../connection';
import type { ConnectionStatus } from '../hooks/use-connection-status';
import { claudeLogin, claudeLogout, pickClaudeBinary } from '../transport/claude-transport';
import { codexLogin, codexLogout, codexModels, pickCodexBinary } from '../transport/codex-transport';
import { deleteKey, saveKey } from '../transport/key-service';

import classes from './assistant.module.scss';

const ApiSettings = ({ status }: { status: ConnectionStatus }) => {
    const connection = useAiConnection();
    const agent = getAiAgent(connection.agentId);
    const [key, setKey] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const account = agent.credentialAccount ?? '';

    const store = () => {
        setIsSaving(true);
        setError(null);
        void saveKey(account, key.trim())
            .then(() => {
                setKey('');
                status.refresh();
            })
            .catch((reason: unknown) => {
                setError(reason instanceof Error ? reason.message : 'The API key could not be stored.');
            })
            .finally(() => setIsSaving(false));
    };

    const remove = () => {
        void deleteKey(account)
            .then(status.refresh)
            .catch((reason: unknown) => {
                setError(reason instanceof Error ? reason.message : 'The API key could not be removed.');
            });
    };

    return (
        <Flex direction='column' gap='size-150'>
            {status.isReady ? (
                <Flex alignItems='center' justifyContent='space-between' gap='size-100'>
                    <Text>API key connected</Text>
                    <Button variant='secondary' onPress={remove}>
                        Remove
                    </Button>
                </Flex>
            ) : (
                <Flex direction='column' gap='size-100'>
                    <TextField
                        width='100%'
                        type='password'
                        label={`${agent.vendor === 'openai' ? 'OpenAI' : 'Anthropic'} API key`}
                        value={key}
                        onChange={setKey}
                    />
                    <Button
                        alignSelf='end'
                        variant='accent'
                        onPress={store}
                        isPending={isSaving}
                        isDisabled={key.trim() === ''}
                    >
                        Save key
                    </Button>
                </Flex>
            )}
            <ComboBox
                width='100%'
                allowsCustomValue
                label='Model'
                inputValue={connection.model}
                onInputChange={(model: string) => setAiConnection({ model })}
            >
                {agent.modelGroups.map((group: AiModelGroup) => (
                    <Section key={group.label} title={group.label}>
                        {group.models.map((model) => (
                            <Item key={model}>{model}</Item>
                        ))}
                    </Section>
                ))}
            </ComboBox>
            {error !== null && (
                <InlineAlert variant='negative' width='100%'>
                    <Content>{error}</Content>
                </InlineAlert>
            )}
        </Flex>
    );
};

const AppSettings = ({ status }: { status: ConnectionStatus }) => {
    const connection = useAiConnection();
    const agent = getAiAgent(connection.agentId);
    const [isBusy, setIsBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [models, setModels] = useState<string[]>([]);
    const modelGroups = groupModelIds(models);

    useEffect(() => {
        if (agent.id !== 'openai-app' || !status.isReady) return;
        let active = true;
        void codexModels().then((items) => {
            if (active) setModels(items.map(({ id }) => id));
        });
        return () => {
            active = false;
        };
    }, [agent.id, status.isReady]);

    const run = (action: () => Promise<void>) => {
        setIsBusy(true);
        setError(null);
        void action()
            .then(status.refresh)
            .catch((reason: unknown) => {
                setError(reason instanceof Error ? reason.message : `${agent.name} could not be reached.`);
            })
            .finally(() => setIsBusy(false));
    };

    const login = () => (agent.id === 'openai-app' ? codexLogin(() => undefined) : claudeLogin());
    const logout = () => (agent.id === 'openai-app' ? codexLogout() : claudeLogout());
    const browse = () => {
        const pick = agent.id === 'openai-app' ? pickCodexBinary : pickClaudeBinary;
        void pick().then((path) => {
            if (path !== null) setAiConnection({ executable: path });
        });
    };

    return (
        <Flex direction='column' gap='size-150'>
            <Flex alignItems='center' justifyContent='space-between' gap='size-100'>
                <Text>
                    {status.isReady
                        ? `Connected${status.account?.email ? ` as ${status.account.email}` : ''}`
                        : 'Not connected'}
                </Text>
                <Button
                    variant={status.isReady ? 'secondary' : 'accent'}
                    isPending={isBusy || status.isLoading}
                    onPress={() => run(status.isReady ? logout : login)}
                >
                    {status.isReady ? 'Sign out' : 'Sign in'}
                </Button>
            </Flex>
            <Flex alignItems='end' gap='size-100'>
                <TextField
                    flex={1}
                    label={`${agent.name} location`}
                    placeholder='Detected automatically'
                    value={connection.executable}
                    onChange={(executable: string) => setAiConnection({ executable })}
                />
                <Button variant='secondary' onPress={browse}>
                    Browse
                </Button>
            </Flex>
            <ComboBox
                width='100%'
                allowsCustomValue
                label='Model'
                inputValue={connection.model}
                onInputChange={(model: string) => setAiConnection({ model })}
            >
                {modelGroups.map((group: AiModelGroup) => (
                    <Section key={group.label} title={group.label}>
                        {group.models.map((model) => (
                            <Item key={model}>{model}</Item>
                        ))}
                    </Section>
                ))}
            </ComboBox>
            {error !== null && (
                <InlineAlert variant='negative' width='100%'>
                    <Content>{error}</Content>
                </InlineAlert>
            )}
        </Flex>
    );
};

export const ConnectionSettings = ({ status }: { status: ConnectionStatus }) => {
    const connection = useAiConnection();
    const agent = getAiAgent(connection.agentId);
    const methods = availableAgentsForVendor(agent.vendor);

    return (
        <div className={classes.connectionPanel}>
            {methods.length > 1 && (
                <div className={classes.connectionMethods} role='radiogroup' aria-label='Connection method'>
                    {methods.map((method) => (
                        <button
                            key={method.id}
                            type='button'
                            role='radio'
                            aria-checked={method.id === agent.id}
                            className={classes.connectionMethod}
                            onClick={() => setAiAgent(method.id)}
                        >
                            <strong>{method.name}</strong>
                            <span>{method.method === 'api' ? 'API key' : 'Desktop app'}</span>
                        </button>
                    ))}
                </div>
            )}
            {agent.method === 'api' ? <ApiSettings status={status} /> : <AppSettings status={status} />}
            {status.error !== null && (
                <InlineAlert variant='negative' width='100%'>
                    <Content>{status.error}</Content>
                </InlineAlert>
            )}
        </div>
    );
};
