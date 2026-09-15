// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from 'react';

import {
    Button,
    ComboBox,
    Content,
    Flex,
    InlineAlert,
    Item,
    Picker,
    Radio,
    RadioGroup,
    Text,
    TextField,
} from '@geti-ui/ui';

import { Link } from '../../../platform/components/link.component';
import { OPENAI_API_KEYS_URL, SUGGESTED_API_MODELS } from '../config';
import { setAiConnection, setAiProvider, useAiConnection } from '../connection';
import type { ConnectionStatus } from '../hooks/use-connection-status';
import { codexLogin, codexLogout, codexModels } from '../transport/codex-transport';
import { deleteKey, saveKey } from '../transport/key-service';
import type { CodexModel } from '../types';

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
    const [isBusy, setIsBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const isSignedIn = status.account !== null;

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

            <TextField
                width={'100%'}
                label={'ChatGPT app location'}
                description={'Leave empty unless the ChatGPT app is installed in a non-standard folder.'}
                value={executable}
                onChange={(value: string) => setAiConnection({ executable: value })}
            />

            {error !== null && (
                <InlineAlert variant={'negative'} width={'100%'}>
                    <Content>{error}</Content>
                </InlineAlert>
            )}
        </Flex>
    );
};

export const ConnectionSettings = ({ status }: { status: ConnectionStatus }) => {
    const { provider } = useAiConnection();

    return (
        <Flex direction={'column'} gap={'size-200'} UNSAFE_className={classes.settings}>
            <RadioGroup
                label={'Connect through'}
                orientation={'horizontal'}
                value={provider}
                onChange={(value: string) => setAiProvider(value === 'chatgpt' ? 'chatgpt' : 'api')}
            >
                <Radio value={'api'}>OpenAI API key</Radio>
                <Radio value={'chatgpt'}>ChatGPT app</Radio>
            </RadioGroup>

            {provider === 'api' ? <ApiKeySettings status={status} /> : <ChatGptSettings status={status} />}

            {status.error !== null && (
                <InlineAlert variant={'negative'} width={'100%'}>
                    <Content>{status.error}</Content>
                </InlineAlert>
            )}
        </Flex>
    );
};
