// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState, type KeyboardEvent } from 'react';

import { useTranslation } from '@/i18n';
import { Button, ComboBox, Content, Flex, InlineAlert, Item, Section, Text, TextField, type Key } from '@geti-ui/ui';

import { availableAgentsForVendor, getAiAgent } from '../agents';
import { groupModelIds, type AiModelGroup } from '../config';
import { setAiAgent, setAiConnection, useAiConnection } from '../connection';
import type { ConnectionStatus } from '../hooks/use-connection-status';
import { hasSecureAiBackend } from '../platform';
import { claudeLogin, claudeLogout, pickClaudeBinary } from '../transport/claude-transport';
import { codexLogin, codexLogout, codexModels, pickCodexBinary } from '../transport/codex-transport';
import { deleteKey, saveKey } from '../transport/key-service';

import classes from './assistant.module.scss';

const ModelSelector = ({ groups }: { groups: readonly AiModelGroup[] }) => {
    const { t } = useTranslation();
    const connection = useAiConnection();
    const [draftModel, setDraftModel] = useState(connection.model);

    // The combobox edits a draft; the connection (and localStorage) is only
    // touched when a model is chosen or the dropdown closes with new text.
    useEffect(() => {
        setDraftModel(connection.model);
    }, [connection.model]);

    return (
        <ComboBox
            width='100%'
            allowsCustomValue
            label={t('common.labels.model')}
            inputValue={draftModel}
            onInputChange={(model: string) => setDraftModel(model)}
            onSelectionChange={(model: Key | null) => {
                if (model !== null) setAiConnection({ model: String(model) });
            }}
            onOpenChange={(isOpen: boolean) => {
                if (!isOpen && draftModel !== connection.model) {
                    setAiConnection({ model: draftModel });
                }
            }}
        >
            {groups.map((group) => (
                <Section key={group.label} title={group.label}>
                    {group.models.map((model) => (
                        <Item key={model}>{model}</Item>
                    ))}
                </Section>
            ))}
        </ComboBox>
    );
};

const ApiSettings = ({ status }: { status: ConnectionStatus }) => {
    const { t } = useTranslation();
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
                setError(reason instanceof Error ? reason.message : t('assistant.keyStoreFailed'));
            })
            .finally(() => setIsSaving(false));
    };

    const remove = () => {
        void deleteKey(account)
            .then(status.refresh)
            .catch((reason: unknown) => {
                setError(reason instanceof Error ? reason.message : t('assistant.keyRemoveFailed'));
            });
    };

    return (
        <Flex direction='column' gap='size-150'>
            {!hasSecureAiBackend() && <Text>{t('assistant.webKeyWarning')}</Text>}
            {status.isReady ? (
                <Flex alignItems='center' justifyContent='space-between' gap='size-100'>
                    <Text>{t('assistant.apiKeyConnected')}</Text>
                    <Button variant='secondary' onPress={remove}>
                        {t('common.actions.remove')}
                    </Button>
                </Flex>
            ) : (
                <Flex direction='column' gap='size-100'>
                    <TextField
                        width='100%'
                        type='password'
                        label={t('assistant.apiKeyLabel', {
                            vendor: agent.vendor === 'openai' ? 'OpenAI' : 'Anthropic',
                        })}
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
                        {t('assistant.saveKey')}
                    </Button>
                </Flex>
            )}
            <ModelSelector groups={agent.modelGroups} />
            {error !== null && (
                <InlineAlert variant='negative' width='100%'>
                    <Content>{error}</Content>
                </InlineAlert>
            )}
        </Flex>
    );
};

const AppSettings = ({ status }: { status: ConnectionStatus }) => {
    const { t } = useTranslation();
    const connection = useAiConnection();
    const agent = getAiAgent(connection.agentId);
    const [isBusy, setIsBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [models, setModels] = useState<string[]>([]);
    const [executable, setExecutable] = useState(connection.executable);
    const modelGroups = groupModelIds(models);

    useEffect(() => {
        setExecutable(connection.executable);
    }, [connection.executable]);

    const commitExecutable = () => {
        if (executable !== connection.executable) {
            setAiConnection({ executable });
        }
    };

    useEffect(() => {
        if (agent.id !== 'openai-app' || !status.isReady) return;
        let active = true;
        void codexModels()
            .then((items) => {
                if (active) setModels(items.map(({ id }) => id));
            })
            .catch((reason: unknown) => {
                console.error('[assistant] the ChatGPT model lookup failed', reason);
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
                setError(
                    reason instanceof Error
                        ? reason.message
                        : t('assistant.agentUnreachable', { assistant: agent.name })
                );
            })
            .finally(() => setIsBusy(false));
    };

    const login = () => (agent.id === 'openai-app' ? codexLogin(() => undefined) : claudeLogin());
    const logout = () => (agent.id === 'openai-app' ? codexLogout() : claudeLogout());
    const browse = () => {
        const pick = agent.id === 'openai-app' ? pickCodexBinary : pickClaudeBinary;
        // The dialog rejects when the user dismisses it, which is not an error.
        void pick()
            .then((path) => {
                if (path !== null) setAiConnection({ executable: path });
            })
            .catch((reason: unknown) => {
                console.error('[assistant] the executable picker failed', reason);
            });
    };

    return (
        <Flex direction='column' gap='size-150'>
            <Flex alignItems='center' justifyContent='space-between' gap='size-100'>
                <Text>
                    {status.isReady
                        ? status.account?.email
                            ? t('assistant.connectedAs', { email: status.account.email })
                            : t('assistant.connected')
                        : t('assistant.notConnected')}
                </Text>
                <Button
                    variant={status.isReady ? 'secondary' : 'accent'}
                    isPending={isBusy || status.isLoading}
                    onPress={() => run(status.isReady ? logout : login)}
                >
                    {status.isReady ? t('assistant.signOut') : t('assistant.signIn')}
                </Button>
            </Flex>
            <Flex alignItems='end' gap='size-100'>
                <TextField
                    flex={1}
                    label={t('assistant.executableLabel', { assistant: agent.name })}
                    placeholder={t('assistant.executablePlaceholder')}
                    value={executable}
                    onChange={(value: string) => setExecutable(value)}
                    onBlur={commitExecutable}
                />
                <Button variant='secondary' onPress={browse}>
                    {t('assistant.browse')}
                </Button>
            </Flex>
            <ModelSelector groups={modelGroups} />
            {error !== null && (
                <InlineAlert variant='negative' width='100%'>
                    <Content>{error}</Content>
                </InlineAlert>
            )}
        </Flex>
    );
};

export const ConnectionSettings = ({ status }: { status: ConnectionStatus }) => {
    const { t } = useTranslation();
    const connection = useAiConnection();
    const agent = getAiAgent(connection.agentId);
    const methods = availableAgentsForVendor(agent.vendor);

    const handleMethodsKeyDown = (event: KeyboardEvent) => {
        if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
        event.preventDefault();
        const group = event.currentTarget as HTMLDivElement;
        const buttons = Array.from(group.querySelectorAll<HTMLButtonElement>('button[role="radio"]'));
        const index = buttons.findIndex((button) => button.getAttribute('aria-checked') === 'true');
        if (index === -1) return;
        const nextMethod = methods[(index + 1) % methods.length];
        const nextButton = buttons[(index + 1) % buttons.length];
        setAiAgent(nextMethod.id);
        nextButton.focus();
    };

    return (
        <div className={classes.connectionPanel}>
            {methods.length > 1 && (
                <div
                    className={classes.connectionMethods}
                    role='radiogroup'
                    aria-label='Connection method'
                    tabIndex={-1}
                    onKeyDown={handleMethodsKeyDown}
                >
                    {methods.map((method) => (
                        <button
                            key={method.id}
                            type='button'
                            role='radio'
                            aria-checked={method.id === agent.id}
                            tabIndex={method.id === agent.id ? 0 : -1}
                            className={classes.connectionMethod}
                            onClick={() => setAiAgent(method.id)}
                        >
                            <strong>{method.name}</strong>
                            <span>{method.method === 'api' ? t('assistant.methodApi') : t('assistant.methodApp')}</span>
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
