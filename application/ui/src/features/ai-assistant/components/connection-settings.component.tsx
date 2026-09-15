// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from 'react';

import { Button, ComboBox, Content, Flex, InlineAlert, Item, Picker, Text, TextArea, TextField } from '@geti-ui/ui';

import { Link } from '../../../platform/components/link.component';
import { OPENAI_API_KEYS_URL, SUGGESTED_API_MODELS } from '../config';
import { setAiConnection, setAiProvider, useAiConnection } from '../connection';
import type { ConnectionStatus } from '../hooks/use-connection-status';
import {
    codexDiagnostics,
    codexLocate,
    codexLogin,
    codexLogout,
    codexModels,
    pickCodexBinary,
} from '../transport/codex-transport';
import { deleteKey, saveKey } from '../transport/key-service';
import type { CodexLocation, CodexModel } from '../types';

import classes from './assistant.module.scss';

const ApiKeySettings = ({ status }: { status: ConnectionStatus }) => {
    const { model } = useAiConnection();

    const [key, setKey] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const store = () => {
        setIsSaving(true);
        setError(null);

        void saveKey(key.trim())
            .then(() => {
                setKey('');
                status.refresh();
            })
            .catch((reason: unknown) => {
                setError(reason instanceof Error ? reason.message : 'The key could not be stored.');
            })
            .finally(() => setIsSaving(false));
    };

    const remove = () => {
        void deleteKey()
            .then(() => status.refresh())
            .catch((reason: unknown) => {
                setError(reason instanceof Error ? reason.message : 'The key could not be removed.');
            });
    };

    return (
        <Flex direction={'column'} gap={'size-150'}>
            {status.hasKey ? (
                <Flex alignItems={'center'} justifyContent={'space-between'} gap={'size-100'}>
                    <Text>Your API key is stored in Windows Credential Manager.</Text>
                    <Button variant={'secondary'} onPress={remove}>
                        Remove
                    </Button>
                </Flex>
            ) : (
                <Flex direction={'column'} gap={'size-100'}>
                    <TextField
                        width={'100%'}
                        type={'password'}
                        label={'OpenAI API key'}
                        description={'Stored in Windows Credential Manager. It is never sent anywhere except OpenAI.'}
                        value={key}
                        onChange={setKey}
                    />
                    <Flex alignItems={'center'} justifyContent={'space-between'} gap={'size-100'}>
                        <Link href={OPENAI_API_KEYS_URL} target={'_blank'} rel={'noopener noreferrer'}>
                            Create a key
                        </Link>
                        <Button variant={'accent'} onPress={store} isPending={isSaving} isDisabled={key.trim() === ''}>
                            Save key
                        </Button>
                    </Flex>
                </Flex>
            )}

            <ComboBox
                width={'100%'}
                allowsCustomValue
                label={'Model'}
                description={'Any model id your key has access to.'}
                inputValue={model}
                onInputChange={(value: string) => setAiConnection({ model: value })}
            >
                {SUGGESTED_API_MODELS.map((suggestion) => (
                    <Item key={suggestion}>{suggestion}</Item>
                ))}
            </ComboBox>

            {error !== null && (
                <InlineAlert variant={'negative'} width={'100%'}>
                    <Content>{error}</Content>
                </InlineAlert>
            )}
        </Flex>
    );
};

const ChatGptSettings = ({ status }: { status: ConnectionStatus }) => {
    const { model, executable } = useAiConnection();

    const [models, setModels] = useState<CodexModel[]>([]);
    const [location, setLocation] = useState<CodexLocation | null>(null);
    const [report, setReport] = useState<string | null>(null);
    const [isBusy, setIsBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const isSignedIn = status.account !== null;

    useEffect(() => {
        let isCurrent = true;

        void codexLocate()
            .then((found) => {
                if (isCurrent) {
                    setLocation(found);
                }
            })
            // Only used to explain where the app was looked for; a failure is not worth reporting.
            .catch(() => undefined);

        return () => {
            isCurrent = false;
        };
    }, [status.account, executable]);

    useEffect(() => {
        if (!isSignedIn) {
            setModels([]);

            return;
        }

        let isCurrent = true;

        void codexModels()
            .then((available) => {
                if (isCurrent) {
                    setModels(available);
                }
            })
            // A failed lookup only costs the dropdown; the account default still works.
            .catch(() => undefined);

        return () => {
            isCurrent = false;
        };
    }, [isSignedIn]);

    const run = (action: () => Promise<void>) => {
        setIsBusy(true);
        setError(null);

        void action()
            .then(() => status.refresh())
            .catch((reason: unknown) => {
                setError(reason instanceof Error ? reason.message : 'The ChatGPT app could not be reached.');
            })
            .finally(() => setIsBusy(false));
    };

    const browse = () => {
        void pickCodexBinary()
            .then((selected) => {
                if (selected !== null) {
                    setAiConnection({ executable: selected });
                    status.refresh();
                }
            })
            .catch((reason: unknown) => {
                setError(reason instanceof Error ? reason.message : 'The file picker could not be opened.');
            });
    };

    const diagnose = () => {
        if (report !== null) {
            setReport(null);

            return;
        }

        void codexDiagnostics()
            .then((text) => {
                setReport(text);
                // A clipboard copy is the fastest way to share the report; the box below is the fallback.
                void navigator.clipboard?.writeText(text).catch(() => undefined);
            })
            .catch((reason: unknown) => {
                setError(reason instanceof Error ? reason.message : 'The diagnostics report could not be collected.');
            });
    };

    return (
        <Flex direction={'column'} gap={'size-150'}>
            <Flex alignItems={'center'} justifyContent={'space-between'} gap={'size-100'}>
                <Text>
                    {status.isLoading
                        ? 'Checking your ChatGPT account…'
                        : status.account === null
                          ? 'Uses your ChatGPT subscription through the ChatGPT (Codex) app.'
                          : `Signed in as ${status.account.email ?? 'your ChatGPT account'}${
                                status.account.plan === null ? '' : ` (${status.account.plan})`
                            }.`}
                </Text>
                <Button
                    variant={isSignedIn ? 'secondary' : 'accent'}
                    isPending={isBusy}
                    onPress={() => run(isSignedIn ? codexLogout : () => codexLogin(() => setError(null)))}
                >
                    {isSignedIn ? 'Sign out' : 'Sign in'}
                </Button>
            </Flex>

            {isSignedIn && models.length > 0 && (
                <Picker
                    width={'100%'}
                    label={'Model'}
                    selectedKey={model === '' ? null : model}
                    placeholder={'Account default'}
                    onSelectionChange={(key) => setAiConnection({ model: String(key) })}
                >
                    {models.map((available) => (
                        <Item key={available.id}>{available.label}</Item>
                    ))}
                </Picker>
            )}

            <Flex direction={'column'} gap={'size-75'}>
                <Flex alignItems={'end'} gap={'size-100'}>
                    <TextField
                        flex={1}
                        label={'ChatGPT app location'}
                        placeholder={location?.path ?? 'Detected automatically'}
                        value={executable}
                        onChange={(value: string) => setAiConnection({ executable: value })}
                    />
                    <Button variant={'secondary'} onPress={browse}>
                        Browse…
                    </Button>
                </Flex>

                {executable === '' && location !== null && (
                    <Text UNSAFE_className={classes.providerHint}>
                        {location.path === null
                            ? `Not found in ${location.searched.length} standard locations, including ` +
                              `${location.searched.slice(0, 2).join(' and ')}. Pick it with Browse instead.`
                            : `Detected at ${location.path}.`}
                    </Text>
                )}
            </Flex>

            <Flex direction={'column'} gap={'size-75'}>
                <Flex alignItems={'center'} justifyContent={'space-between'} gap={'size-100'}>
                    <Text UNSAFE_className={classes.providerHint}>
                        Sign-in trouble? The report shows where Codex was found and what it answered.
                    </Text>
                    <Button variant={'secondary'} onPress={diagnose}>
                        {report === null ? 'Diagnostics' : 'Hide'}
                    </Button>
                </Flex>

                {report !== null && (
                    <TextArea
                        width={'100%'}
                        height={'size-2400'}
                        isReadOnly
                        aria-label={'ChatGPT diagnostics report'}
                        description={'Copied to the clipboard. Attach it when reporting a sign-in problem.'}
                        value={report}
                    />
                )}
            </Flex>

            {error !== null && (
                <InlineAlert variant={'negative'} width={'100%'}>
                    <Content>{error}</Content>
                </InlineAlert>
            )}
        </Flex>
    );
};

interface ProviderCardProps {
    title: string;
    hint: string;
    isSelected: boolean;
    isConnected: boolean;
    onSelect: () => void;
}

const ProviderCard = ({ title, hint, isSelected, isConnected, onSelect }: ProviderCardProps) => (
    <button
        type={'button'}
        aria-pressed={isSelected}
        className={[classes.providerCard, isSelected ? classes.providerCardSelected : ''].join(' ').trim()}
        onClick={onSelect}
    >
        <span className={classes.providerTitle}>{title}</span>
        <span className={classes.providerHint}>{hint}</span>
        <span
            className={[
                classes.providerState,
                classes.providerStateCard,
                isConnected ? classes.providerStateConnected : '',
            ]
                .join(' ')
                .trim()}
        >
            {isConnected ? 'Connected' : 'Not connected'}
        </span>
    </button>
);

export const ConnectionSettings = ({ status }: { status: ConnectionStatus }) => {
    const { provider } = useAiConnection();

    return (
        <Flex direction={'column'} gap={'size-200'} UNSAFE_className={classes.settings}>
            <Flex direction={'column'} gap={'size-100'}>
                <Text UNSAFE_className={classes.settingsLabel}>Connect through</Text>

                <div className={classes.providerChoice}>
                    <ProviderCard
                        title={'OpenAI API key'}
                        hint={'Billed per request'}
                        isSelected={provider === 'api'}
                        isConnected={status.hasKey}
                        onSelect={() => setAiProvider('api')}
                    />
                    <ProviderCard
                        title={'ChatGPT app'}
                        hint={'Uses your subscription'}
                        isSelected={provider === 'chatgpt'}
                        isConnected={status.account !== null}
                        onSelect={() => setAiProvider('chatgpt')}
                    />
                </div>
            </Flex>

            {provider === 'api' ? <ApiKeySettings status={status} /> : <ChatGptSettings status={status} />}

            {status.error !== null && (
                <InlineAlert variant={'negative'} width={'100%'}>
                    <Content>{status.error}</Content>
                </InlineAlert>
            )}
        </Flex>
    );
};
